import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { LoadingState, EmptyState } from "@/components/States";
import { useToast } from "@/components/Toast";
import { createJobDescription, analyzeJobDescription, listJobDescriptions } from "@/api/jobs";
import { apiErrorMessage } from "@/api/client";

export default function JobDescriptionPage() {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { show } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: jobs, isLoading } = useQuery({ queryKey: ["jobs"], queryFn: listJobDescriptions });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (text.trim().length < 20) {
      show("error", "Please paste the full job description.");
      return;
    }
    setSubmitting(true);
    try {
      const jd = await createJobDescription({ title, company_name: company || undefined, raw_text: text });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      try {
        show("info", "Analyzing job requirements...");
        await analyzeJobDescription(jd.id);
        show("success", "Job description analyzed.");
      } catch (analyzeErr) {
        // The job description itself is safely saved either way - only the
        // AI extraction step failed. Land on its Analysis page, which has
        // its own "Analyze job description" retry action for exactly this
        // case, so nothing is lost and there's no dead end here.
        show("error", `Saved, but analysis failed: ${apiErrorMessage(analyzeErr)}`);
      }
      navigate(`/analysis/${jd.id}`);
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Layout>
      <PageHeader title="Job Description" subtitle="Paste the job you're targeting so we can match your profile against it." />

      <div className="grid lg:grid-cols-2 gap-6">
        <form onSubmit={handleSubmit} className="card space-y-4 h-fit">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Job title</label>
              <input required className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Senior Backend Engineer" />
            </div>
            <div>
              <label className="label">Company (optional)</label>
              <input className="input" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Acme Corp" />
            </div>
          </div>
          <div>
            <label className="label">Job description</label>
            <textarea
              required
              className="input min-h-[260px]"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the full job description here..."
            />
          </div>
          <button type="submit" disabled={submitting} className="btn-primary w-full">
            <Sparkles className="w-4 h-4" />
            {submitting ? "Analyzing..." : "Save & Analyze"}
          </button>
        </form>

        <div className="card">
          <h2 className="font-semibold mb-4">Saved Job Descriptions</h2>
          {isLoading && <LoadingState />}
          {jobs && jobs.length === 0 && <EmptyState title="No job descriptions yet" description="Save one to run your first analysis." />}
          {jobs && jobs.length > 0 && (
            <ul className="divide-y divide-border">
              {jobs.map((jd) => (
                <li key={jd.id} className="py-3">
                  <button className="text-left w-full hover:text-primary-700" onClick={() => navigate(`/analysis/${jd.id}`)}>
                    <div className="font-medium text-sm">{jd.title}</div>
                    <div className="text-xs text-ink-muted">{jd.company_name || "No company specified"}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Layout>
  );
}
