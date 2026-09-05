import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, Check } from "lucide-react";
import clsx from "clsx";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { LoadingState } from "@/components/States";
import { useToast } from "@/components/Toast";
import { listJobDescriptions } from "@/api/jobs";
import { listTemplates, generateResume } from "@/api/generator";
import { apiErrorMessage } from "@/api/client";

const ALL_SECTIONS = ["summary", "skills", "experience", "projects", "education", "certifications", "achievements"];

export default function Generator() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { show } = useToast();

  const [jdId, setJdId] = useState(params.get("jd") ?? "");
  const [templateSlug, setTemplateSlug] = useState("ats_classic");
  const [versionName, setVersionName] = useState("");
  const [sections, setSections] = useState<string[]>(ALL_SECTIONS);
  const [generating, setGenerating] = useState(false);

  const { data: jobs, isLoading: jobsLoading } = useQuery({ queryKey: ["jobs"], queryFn: listJobDescriptions });
  const { data: templates, isLoading: templatesLoading } = useQuery({ queryKey: ["templates"], queryFn: listTemplates });

  function toggleSection(section: string) {
    setSections((prev) => (prev.includes(section) ? prev.filter((s) => s !== section) : [...prev, section]));
  }

  async function handleGenerate() {
    if (!jdId) {
      show("error", "Select a job description first.");
      return;
    }
    setGenerating(true);
    try {
      show("info", "Generating tailored resume...");
      const generated = await generateResume({
        job_description_id: jdId,
        template_slug: templateSlug,
        version_name: versionName || "Untitled Resume",
        sections,
      });
      show("success", "Resume generated.");
      navigate(`/editor/${generated.id}`);
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Layout>
      <PageHeader title="Resume Generator" subtitle="Choose a template and target job, and we'll build a tailored, ATS-friendly resume." />

      {(jobsLoading || templatesLoading) && <LoadingState />}

      {jobs && templates && (
        <div className="space-y-6 max-w-2xl">
          <div className="card">
            <label className="label">Target job description</label>
            <select className="input" value={jdId} onChange={(e) => setJdId(e.target.value)}>
              <option value="">Select a job description...</option>
              {jobs.map((jd) => (
                <option key={jd.id} value={jd.id}>{jd.title}{jd.company_name ? ` — ${jd.company_name}` : ""}</option>
              ))}
            </select>

            <label className="label mt-4">Version name</label>
            <input className="input" placeholder="e.g. Backend Engineer @ Acme" value={versionName} onChange={(e) => setVersionName(e.target.value)} />
          </div>

          <div className="card">
            <h2 className="font-semibold mb-3">Template</h2>
            <div className="grid sm:grid-cols-3 gap-3">
              {templates.map((t) => (
                <button
                  key={t.slug}
                  onClick={() => setTemplateSlug(t.slug)}
                  className={clsx(
                    "text-left border rounded-lg p-3 transition-colors",
                    templateSlug === t.slug ? "border-primary-600 bg-primary-50" : "border-border hover:border-primary-300"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{t.name}</span>
                    {templateSlug === t.slug && <Check className="w-4 h-4 text-primary-700" />}
                  </div>
                  <p className="text-xs text-ink-muted mt-1">{t.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-3">Sections to include</h2>
            <div className="flex flex-wrap gap-2">
              {ALL_SECTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => toggleSection(s)}
                  className={sections.includes(s) ? "btn-primary" : "btn-secondary"}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <button className="btn-primary w-full" onClick={handleGenerate} disabled={generating}>
            <Sparkles className="w-4 h-4" /> {generating ? "Generating..." : "Generate tailored resume"}
          </button>
        </div>
      )}
    </Layout>
  );
}
