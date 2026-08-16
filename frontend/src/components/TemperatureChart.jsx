import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatTick(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("es-AR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export default function TemperatureChart({ readings, tempMin, tempMax }) {
  const data = readings
    .filter((r) => r.temperatura !== null && r.temperatura !== undefined)
    .map((r) => ({ ts: r.timestamp, temp: r.temperatura }));

  if (data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate-400">
        Sin lecturas de temperatura todavía
      </div>
    );
  }

  const hasRange = tempMin !== null && tempMax !== null && tempMin !== undefined && tempMax !== undefined;

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="ts" tickFormatter={formatTick} minTickGap={80} tick={{ fontSize: 11 }} />
          <YAxis
            tick={{ fontSize: 11 }}
            domain={["auto", "auto"]}
            tickFormatter={(v) => `${v}°`}
            width={45}
          />
          <Tooltip
            labelFormatter={formatTick}
            formatter={(v) => [`${Number(v).toFixed(1)}°C`, "Temperatura"]}
          />
          {hasRange && (
            <ReferenceArea y1={tempMin} y2={tempMax} fill="#22c55e" fillOpacity={0.12} />
          )}
          {hasRange && (
            <>
              <ReferenceLine y={tempMin} stroke="#16a34a" strokeDasharray="4 4" />
              <ReferenceLine y={tempMax} stroke="#16a34a" strokeDasharray="4 4" />
            </>
          )}
          <Line
            type="monotone"
            dataKey="temp"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
