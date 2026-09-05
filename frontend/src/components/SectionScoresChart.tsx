import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";

function colorFor(score: number) {
  if (score >= 80) return "#16A34A";
  if (score >= 50) return "#D97706";
  return "#DC2626";
}

export default function SectionScoresChart({ sectionScores }: { sectionScores: Record<string, number> }) {
  const data = Object.entries(sectionScores).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    score: value,
  }));

  return (
    <div className="card">
      <h2 className="font-semibold mb-2">Resume Section Scores</h2>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 12, fill: "#475569" }} axisLine={false} tickLine={false} />
            <Tooltip />
            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={16}>
              {data.map((entry, i) => (
                <Cell key={i} fill={colorFor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
