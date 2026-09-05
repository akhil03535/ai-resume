import { PieChart, Pie, Cell } from "recharts";

function colorFor(score: number) {
  if (score >= 80) return "#16A34A";
  if (score >= 55) return "#D97706";
  return "#DC2626";
}

export default function ScoreGauge({
  score,
  label,
  size = 140,
}: {
  score: number;
  label: string;
  size?: number;
}) {
  const data = [
    { value: score },
    { value: 100 - score },
  ];
  const color = colorFor(score);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <PieChart width={size} height={size}>
          <Pie
            data={data}
            dataKey="value"
            startAngle={90}
            endAngle={-270}
            innerRadius={size / 2 - 14}
            outerRadius={size / 2}
            stroke="none"
          >
            <Cell fill={color} />
            <Cell fill="#E2E8F0" />
          </Pie>
        </PieChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-ink">{score}</span>
          <span className="text-xs text-ink-muted">/ 100</span>
        </div>
      </div>
      <span className="text-sm font-medium text-ink-muted mt-2">{label}</span>
    </div>
  );
}
