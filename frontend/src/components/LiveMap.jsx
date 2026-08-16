import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Los iconos por defecto de Leaflet se rompen con bundlers; re-registrarlos.
import iconRetina from "leaflet/dist/images/marker-icon-2x.png";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

L.Marker.prototype.options.icon = L.icon({
  iconUrl,
  iconRetinaUrl: iconRetina,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export default function LiveMap({ points }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);

  // Inicializar el mapa una sola vez.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, { attributionControl: true }).setView([-20, -10], 3);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Redibujar ruta + marcador cuando cambian los puntos.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Polyline) map.removeLayer(layer);
    });
    const valid = points.filter((p) => p.lat !== null && p.lat !== undefined && p.lng !== null && p.lng !== undefined);
    if (valid.length === 0) return;
    const latlngs = valid.map((p) => [p.lat, p.lng]);
    L.polyline(latlngs, { color: "#2563eb", weight: 3, opacity: 0.8 }).addTo(map);
    const last = valid[valid.length - 1];
    L.marker([last.lat, last.lng])
      .addTo(map)
      .bindPopup(
        `Última posición<br/>${new Date(last.timestamp).toLocaleString("es-AR")}`
      )
      .openPopup();
    map.fitBounds(L.latLngBounds(latlngs).pad(0.3), { maxZoom: 14 });
  }, [points]);

  if (points.filter((p) => p.lat != null).length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate-400">
        Sin datos de ubicación
      </div>
    );
  }

  return <div ref={containerRef} className="h-72 w-full rounded-lg border border-slate-200" />;
}
