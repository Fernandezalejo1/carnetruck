"""Generación de certificados de cadena de frío.

Motor primario: WeasyPrint (HTML+SVG → PDF, incluye gráfico de temperatura).
Fallback: generador PDF mínimo en Python puro (sin dependencias), para que el
endpoint funcione aunque WeasyPrint no esté instalado (p. ej. dev sin Docker).
"""

import html
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Alert, Certificate, Reading, Shipment
from .integrity_hash import document_hash, normalized_iso

logger = logging.getLogger(__name__)

_MAX_CHART_POINTS = 500


# ---------------------------------------------------------------- estadísticas

def _certificate_stats(db: Session, shipment: Shipment) -> dict:
    readings = (
        db.query(Reading)
        .filter(Reading.shipment_id == shipment.id)
        .order_by(Reading.timestamp.asc())
        .all()
    )
    temps = [r.temperatura for r in readings if r.temperatura is not None]
    n_alerts = (
        db.query(Alert).filter(Alert.shipment_id == shipment.id).count()
    )
    return {
        "readings": readings,
        "count": len(readings),
        "temps": temps,
        "min": min(temps) if temps else None,
        "max": max(temps) if temps else None,
        "avg": (sum(temps) / len(temps)) if temps else None,
        "alerts": n_alerts,
    }


# ------------------------------------------------------------------ gráfico SVG

def _build_svg(readings: list[Reading], temp_min: float | None, temp_max: float | None) -> str:
    points = [(r.timestamp, r.temperatura) for r in readings if r.temperatura is not None]
    if len(points) > _MAX_CHART_POINTS:
        # Downsampling: conservar primero y último, muestrear el resto uniformemente.
        step = (len(points) - 1) / (_MAX_CHART_POINTS - 1)
        points = [points[int(i * step)] for i in range(_MAX_CHART_POINTS)]
    if not points:
        return "<p>Sin lecturas de temperatura.</p>"

    W, H, PAD = 760, 260, 40
    values = [p[1] for p in points]
    lo, hi = min(values + ([temp_min] if temp_min is not None else [])), max(
        values + ([temp_max] if temp_max is not None else [])
    )
    span = hi - lo
    if span <= 0:
        span = 1.0
    lo -= span * 0.1
    hi += span * 0.1

    def x(i: int) -> float:
        return PAD + (i * (W - 2 * PAD) / max(len(points) - 1, 1))

    def y(v: float) -> float:
        return H - PAD - ((v - lo) / (hi - lo)) * (H - 2 * PAD)

    parts = []
    # Banda del rango aceptable
    if temp_min is not None and temp_max is not None:
        band = (
            f'<rect x="{PAD}" y="{y(temp_max):.1f}" width="{W - 2 * PAD:.1f}" '
            f'height="{y(temp_min) - y(temp_max):.1f}" fill="#22c55e" fill-opacity="0.15"/>'
        )
        parts.append(band)
        parts.append(f'<line x1="{PAD}" y1="{y(temp_min):.1f}" x2="{W - PAD}" y2="{y(temp_min):.1f}" stroke="#16a34a" stroke-dasharray="4 4"/>')
        parts.append(f'<line x1="{PAD}" y1="{y(temp_max):.1f}" x2="{W - PAD}" y2="{y(temp_max):.1f}" stroke="#16a34a" stroke-dasharray="4 4"/>')

    # Línea de temperatura
    coords = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(points))
    parts.append(f'<polyline points="{coords}" fill="none" stroke="#2563eb" stroke-width="2"/>')

    # Etiquetas de ejes
    parts.append(f'<text x="{PAD}" y="{y(lo):.1f}" font-size="11" fill="#6b7280">{lo:.1f}°C</text>')
    parts.append(f'<text x="{PAD}" y="{y(hi):.1f}" font-size="11" fill="#6b7280">{hi:.1f}°C</text>')
    first, last = points[0][0], points[-1][0]
    parts.append(f'<text x="{PAD}" y="{H - 12}" font-size="11" fill="#6b7280">{first.strftime("%d/%m %H:%M")}</text>')
    parts.append(f'<text x="{W - PAD}" y="{H - 12}" font-size="11" fill="#6b7280" text-anchor="end">{last.strftime("%d/%m %H:%M")}</text>')

    return (
        f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'
    )


# ------------------------------------------------------------------- render PDF

def _render_weasyprint(html_doc: str) -> bytes | None:
    try:
        from weasyprint import HTML  # import tardío: dependencia opcional

        return HTML(string=html_doc).write_pdf()
    except Exception:
        logger.exception("WeasyPrint falló; usando fallback simple")
        return None


def _simple_text_pdf(title: str, lines: list[str]) -> bytes:
    """PDF mínimo válido (PDF 1.4, una página, Helvetica) sin dependencias."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream_lines = [
        "BT",
        "/F1 14 Tf",
        "50 790 Td",
        f"({esc(title)}) Tj",
        "0 -28 Td",
        "/F1 10 Tf",
    ]
    for line in lines[:40]:
        stream_lines.append(f"({esc(line)}) Tj")
        stream_lines.append("0 -16 Td")
    if len(lines) > 40:
        stream_lines.append(f"(... {len(lines) - 40} líneas adicionales omitidas) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode()
        out += obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


def render_pdf(title: str, lines: list[str], html_doc: str) -> bytes:
    settings = get_settings()
    if settings.pdf_engine in ("weasyprint", "auto"):
        pdf = _render_weasyprint(html_doc)
        if pdf is not None:
            return pdf
    return _simple_text_pdf(title, lines)


# ------------------------------------------------------------------- generación

def generate_certificate(db: Session, shipment: Shipment, regenerate: bool = False) -> Certificate:
    if not regenerate:
        existing = (
            db.query(Certificate)
            .filter(Certificate.shipment_id == shipment.id)
            .order_by(Certificate.generado_en.desc())
            .first()
        )
        if existing:
            return existing

    stats = _certificate_stats(db, shipment)
    now = datetime.now(timezone.utc)

    extra = {
        "shipment_id": shipment.id,
        "numero_contenedor": shipment.numero_contenedor,
        "destino": f"{shipment.destino_pais} ({shipment.mercado})",
        "producto": shipment.tipo_producto,
        "generado_en": normalized_iso(now),
        "temp_min": stats["min"],
        "temp_max": stats["max"],
        "temp_promedio": stats["avg"],
        "alertas": stats["alerts"],
        "lecturas": stats["count"],
    }
    doc_hash = document_hash([r.hash_actual for r in stats["readings"]], extra)

    fmt = "%d/%m/%Y %H:%M"
    title = f"Certificado de Cadena de Frío — Contenedor {shipment.numero_contenedor}"
    lines = [
        f"Contenedor: {shipment.numero_contenedor}",
        f"Destino: {shipment.destino_pais} (mercado {shipment.mercado})",
        f"Producto: {shipment.tipo_producto}",
        f"Rango configurado: {_fmt_temp(shipment.temp_min)} a {_fmt_temp(shipment.temp_max)} °C",
        f"Periodo: {_fmt_dt(shipment.fecha_salida, fmt)} → {_fmt_dt(shipment.fecha_llegada_estimada, fmt)}",
        "",
        f"Lecturas: {stats['count']}",
        f"Temp mínima registrada: {_fmt_temp(stats['min'])} °C",
        f"Temp máxima registrada: {_fmt_temp(stats['max'])} °C",
        f"Temp promedio: {_fmt_temp(stats['avg'])} °C",
        f"Alertas totales: {stats['alerts']}",
        "",
        f"Hash del documento (SHA-256): {doc_hash}",
        f"Generado: {now.strftime(fmt)}",
    ]

    chart = _build_svg(stats["readings"], shipment.temp_min, shipment.temp_max)
    e = html.escape
    html_doc = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
  body {{ font-family: 'DejaVu Sans', Helvetica, Arial, sans-serif; margin: 32px; color: #111827; }}
  h1 {{ font-size: 20px; border-bottom: 3px solid #2563eb; padding-bottom: 8px; }}
  h2 {{ font-size: 15px; margin-top: 24px; color: #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
  th, td {{ border: 1px solid #d1d5db; padding: 6px 10px; font-size: 12px; text-align: left; }}
  th {{ background: #f3f4f6; }}
  .hash {{ font-family: monospace; font-size: 11px; word-break: break-all; background: #f9fafb; padding: 8px; }}
  .muted {{ color: #6b7280; font-size: 12px; }}
</style></head><body>
<h1>{e(title)}</h1>
<table>
  <tr><th>Contenedor</th><td>{e(shipment.numero_contenedor)}</td>
      <th>Destino</th><td>{e(shipment.destino_pais)} ({e(shipment.mercado)})</td></tr>
  <tr><th>Producto</th><td>{e(shipment.tipo_producto)}</td>
      <th>Rango</th><td>{_fmt_temp(shipment.temp_min)} a {_fmt_temp(shipment.temp_max)} °C</td></tr>
  <tr><th>Salida</th><td>{_fmt_dt(shipment.fecha_salida, fmt)}</td>
      <th>Llegada estimada</th><td>{_fmt_dt(shipment.fecha_llegada_estimada, fmt)}</td></tr>
</table>
<h2>Evolución de temperatura</h2>
{chart}
<h2>Estadísticas</h2>
<table>
  <tr><th>Lecturas</th><td>{stats['count']}</td>
      <th>Alertas</th><td>{stats['alerts']}</td></tr>
  <tr><th>Mínima</th><td>{_fmt_temp(stats['min'])} °C</td>
      <th>Máxima</th><td>{_fmt_temp(stats['max'])} °C</td>
      <th>Promedio</th><td>{_fmt_temp(stats['avg'])} °C</td></tr>
</table>
<h2>Integridad</h2>
<p class="muted">Hash encadenado por lectura (SHA-256). El hash del documento cubre
la cadena completa de lecturas y estos metadatos.</p>
<p class="hash">{doc_hash}</p>
<p class="muted">Generado: {now.strftime(fmt)} · Plataforma Carnetruck</p>
</body></html>"""

    pdf_bytes = render_pdf(title, lines, html_doc)

    cert = Certificate(
        shipment_id=shipment.id,
        generado_en=now,
        hash_documento=doc_hash,
        temp_min_registrada=stats["min"],
        temp_max_registrada=stats["max"],
        temp_promedio=stats["avg"],
        cantidad_alertas=stats["alerts"],
        cantidad_lecturas=stats["count"],
        pdf_bytes=pdf_bytes,
        url_pdf="",  # se completa tras insertar (necesita el id)
    )
    db.add(cert)
    db.flush()
    cert.url_pdf = f"/api/v1/certificates/{cert.id}/pdf"
    db.commit()
    db.refresh(cert)
    return cert


def _fmt_temp(v: float | None) -> str:
    return f"{v:.1f}" if v is not None else "—"


def _fmt_dt(v: datetime | None, fmt: str) -> str:
    return v.strftime(fmt) if v is not None else "—"
