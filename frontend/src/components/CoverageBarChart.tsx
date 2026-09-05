import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from "recharts";

export default function CoverageBarChart({
  title,
  matched,
  partial,
  missing,
}: {
  title: string;
  matched: number;
  partial: number;
  missing: number;
}) {
  const data = [{ name: title, Matched: matched, Partial: partial, Missing: missing }];

  return (
    <div className="card">
      <h2 className="font-semibold mb-2">{title}</h2>
      <div className="h-28">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 0, right: 10 }}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" hide />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Matched" stackId="a" fill="#16A34A" radius={[4, 0, 0, 4]} />
            <Bar dataKey="Partial" stackId="a" fill="#D97706" />
            <Bar dataKey="Missing" stackId="a" fill="#DC2626" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
