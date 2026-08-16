from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Certificate, Shipment, User
from ..schemas.certificate import CertificateOut, CertificateVerifyOut
from ..services.certificate_generator import _certificate_stats
from ..services.integrity_hash import document_hash, normalized_iso
from .deps import get_current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])


def _to_out(cert: Certificate) -> CertificateOut:
    out = CertificateOut.model_validate(cert)
    out.numero_contenedor = cert.shipment.numero_contenedor
    return out


def _tenant_ok(user: User, cert: Certificate) -> bool:
    if user.tenant_id is None:
        return True
    return cert.shipment.tenant_id == user.tenant_id


def _get_cert(db: Session, user: User, cert_id: int) -> Certificate:
    cert = db.get(Certificate, cert_id)
    if cert is None or not _tenant_ok(user, cert):
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return cert


@router.get("", response_model=list[CertificateOut])
def list_certificates(
    shipment_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CertificateOut]:
    q = db.query(Certificate).join(Shipment)
    if user.tenant_id is not None:
        q = q.filter(Shipment.tenant_id == user.tenant_id)
    if shipment_id is not None:
        q = q.filter(Certificate.shipment_id == shipment_id)
    certs = q.order_by(Certificate.generado_en.desc()).offset(offset).limit(limit).all()
    return [_to_out(c) for c in certs]


@router.get("/{cert_id}", response_model=CertificateOut)
def get_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CertificateOut:
    return _to_out(_get_cert(db, user, cert_id))


@router.get("/{cert_id}/pdf")
def download_pdf(
    cert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    cert = _get_cert(db, user, cert_id)
    if not cert.pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF no disponible")
    filename = f"certificado_{cert.shipment.numero_contenedor}_{cert.id}.pdf"
    return StreamingResponse(
        iter([cert.pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/{cert_id}/verify", response_model=CertificateVerifyOut)
def verify_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CertificateVerifyOut:
    cert = _get_cert(db, user, cert_id)
    shipment = cert.shipment
    stats = _certificate_stats(db, shipment)
    extra = {
        "shipment_id": shipment.id,
        "numero_contenedor": shipment.numero_contenedor,
        "destino": f"{shipment.destino_pais} ({shipment.mercado})",
        "producto": shipment.tipo_producto,
        "generado_en": normalized_iso(cert.generado_en),
        "temp_min": stats["min"],
        "temp_max": stats["max"],
        "temp_promedio": stats["avg"],
        "alertas": stats["alerts"],
        "lecturas": stats["count"],
    }
    recomputed = document_hash([r.hash_actual for r in stats["readings"]], extra)
    valid = recomputed == cert.hash_documento
    return CertificateVerifyOut(
        valid=valid,
        stored_hash=cert.hash_documento,
        recomputed_hash=recomputed,
        detail="El certificado es íntegro" if valid else "El certificado fue alterado o los datos cambiaron",
    )
