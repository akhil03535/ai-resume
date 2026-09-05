import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

export default function CategoryRadar({ categoryScores }: { categoryScores: Record<string, number> }) {
  const data = Object.entries(categoryScores).map(([key, value]) => ({
    category: key.charAt(0).toUpperCase() + key.slice(1),
    score: value,
  }));

  return (
    <div className="card">
      <h2 className="font-semibold mb-2">Category Breakdown</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="70%">
            <PolarGrid stroke="#E2E8F0" />
            <PolarAngleAxis dataKey="category" tick={{ fill: "#475569", fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
            <Radar dataKey="score" stroke="#2563EB" fill="#2563EB" fillOpacity={0.25} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
