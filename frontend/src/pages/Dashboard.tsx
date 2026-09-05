import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { FileText, Sparkles, TrendingUp, Target } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import { LoadingState, EmptyState, ErrorState } from "@/components/States";
import { getDashboard } from "@/api/dashboard";
import { apiErrorMessage } from "@/api/client";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });

  return (
    <Layout>
      <PageHeader
        title="Career Overview"
        subtitle="Your resume performance at a glance."
        actions={
          <Link to="/upload" className="btn-primary">
            <Sparkles className="w-4 h-4" /> Start new analysis
          </Link>
        }
      />

      {isLoading && <LoadingState message="Loading your dashboard..." />}
      {error && <ErrorState message={apiErrorMessage(error)} />}

      {data && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Latest ATS Score" value={data.latest_ats_score ?? "—"} icon={<Target className="w-5 h-5" />} />
            <StatCard label="Latest Job Match" value={data.latest_job_match_score ? `${data.latest_job_match_score}%` : "—"} icon={<TrendingUp className="w-5 h-5" />} />
            <StatCard label="Profile Completeness" value={`${data.resume_completeness}%`} />
            <StatCard label="Generated Resumes" value={data.generated_resume_count} icon={<FileText className="w-5 h-5" />} />
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card">
              <h2 className="font-semibold text-ink mb-3">Recent Analyses</h2>
              {data.recent_analyses.length === 0 ? (
                <EmptyState title="No analyses yet" description="Upload a resume and add a job description to get started." />
              ) : (
                <ul className="divide-y divide-border">
                  {data.recent_analyses.map((a) => (
                    <li key={a.id} className="py-3 flex items-center justify-between text-sm">
                      <span className="text-ink-muted">{new Date(a.created_at).toLocaleDateString()}</span>
                      <span className="font-medium">ATS {a.ats_score} · Match {a.job_match_score}%</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card">
              <h2 className="font-semibold text-ink mb-3">Recent Generated Resumes</h2>
              {data.recent_generated_resumes.length === 0 ? (
                <EmptyState title="No resumes generated yet" description="Once you analyze a job match, you can generate a tailored resume." />
              ) : (
                <ul className="divide-y divide-border">
                  {data.recent_generated_resumes.map((g) => (
                    <li key={g.id} className="py-3 flex items-center justify-between text-sm">
                      <span className="truncate">{g.version_name}</span>
                      <span className="font-medium">{g.ats_score ?? "—"}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {data.top_recommendations.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-ink mb-3">Top Recommendations</h2>
              <ul className="space-y-2">
                {data.top_recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-ink-muted flex items-start gap-2">
                    <span className={r.severity === "ISSUE" ? "text-danger mt-0.5" : "text-warning mt-0.5"}>•</span>
                    {r.text}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
