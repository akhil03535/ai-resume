import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Download, RefreshCw, Save, Sparkles, Wand2 } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { LoadingState } from "@/components/States";
import { useToast } from "@/components/Toast";
import {
  getGeneratedResume,
  updateGeneratedResume,
  reanalyzeGeneratedResume,
  improveBullet,
  exportPdfUrl,
  exportDocxUrl,
} from "@/api/generator";
import { api, apiErrorMessage } from "@/api/client";

const IMPROVE_MODES = [
  { value: "improve", label: "Improve" },
  { value: "concise", label: "Concise" },
  { value: "ats_friendly", label: "ATS-friendly" },
  { value: "technical", label: "Technical" },
  { value: "impact", label: "Impact" },
];

export default function Editor() {
  const { resumeId } = useParams<{ resumeId: string }>();
  const { show } = useToast();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["generated", resumeId],
    queryFn: () => getGeneratedResume(resumeId!),
    enabled: !!resumeId,
  });

  const [content, setContent] = useState<any>(null);
  const [versionName, setVersionName] = useState("");
  const [saving, setSaving] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [improvingKey, setImprovingKey] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setContent(data.content);
      setVersionName(data.version_name);
    }
  }, [data]);

  if (isLoading || !content) return <Layout><LoadingState message="Loading editor..." /></Layout>;

  function updateBullet(section: "experience" | "projects", itemIndex: number, bulletIndex: number, value: string) {
    const copy = { ...content };
    copy[section] = [...copy[section]];
    copy[section][itemIndex] = { ...copy[section][itemIndex] };
    copy[section][itemIndex].bullets = [...copy[section][itemIndex].bullets];
    copy[section][itemIndex].bullets[bulletIndex] = value;
    setContent(copy);
  }

  async function handleImprove(section: "experience" | "projects", itemIndex: number, bulletIndex: number, mode: string) {
    const key = `${section}-${itemIndex}-${bulletIndex}`;
    setImprovingKey(key);
    try {
      const original = content[section][itemIndex].bullets[bulletIndex];
      const result = await improveBullet(original, mode);
      updateBullet(section, itemIndex, bulletIndex, result.improved_text);
      show("success", "Bullet updated.");
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setImprovingKey(null);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updateGeneratedResume(resumeId!, content, versionName);
      show("success", "Version saved.");
      refetch();
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleReanalyze() {
    setReanalyzing(true);
    try {
      await updateGeneratedResume(resumeId!, content, versionName);
      await reanalyzeGeneratedResume(resumeId!);
      show("success", "Re-analyzed with your edits.");
      refetch();
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setReanalyzing(false);
    }
  }

  async function handleDownload(kind: "pdf" | "docx") {
    try {
      const url = kind === "pdf" ? exportPdfUrl(resumeId!) : exportDocxUrl(resumeId!);
      const response = await api.get(url, { responseType: "blob" });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${versionName || "resume"}.${kind}`;
      link.click();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      show("error", apiErrorMessage(err));
    }
  }

  return (
    <Layout>
      <PageHeader
        title="Resume Editor"
        actions={
          <div className="flex flex-wrap gap-2">
            <button className="btn-secondary" onClick={handleReanalyze} disabled={reanalyzing}>
              <RefreshCw className="w-4 h-4" /> {reanalyzing ? "Re-analyzing..." : "Re-analyze"}
            </button>
            <button className="btn-secondary" onClick={handleSave} disabled={saving}>
              <Save className="w-4 h-4" /> {saving ? "Saving..." : "Save"}
            </button>
            <button className="btn-secondary" onClick={() => handleDownload("docx")}>
              <Download className="w-4 h-4" /> DOCX
            </button>
            <button className="btn-primary" onClick={() => handleDownload("pdf")}>
              <Download className="w-4 h-4" /> PDF
            </button>
          </div>
        }
      />

      {data && (data.ats_score !== null || data.source_ats_score !== null) && (
        <div className="card mb-6 flex items-center gap-6">
          <div>
            <div className="text-xs text-ink-muted">ATS Score</div>
            {data.source_ats_score != null ? (
              <div className="flex items-center gap-2 text-lg font-semibold">
                <span className="text-ink-muted line-through text-base">{data.source_ats_score}</span>
                <span>→</span>
                <span className="text-success">{data.ats_score}</span>
                <span className="text-success text-sm">(+{(data.ats_score ?? 0) - data.source_ats_score})</span>
              </div>
            ) : (
              <div className="text-lg font-semibold">{data.ats_score}</div>
            )}
          </div>
          <div>
            <div className="text-xs text-ink-muted">Job Match</div>
            <div className="text-lg font-semibold">{data.job_match_score}%</div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Editor */}
        <div className="space-y-4">
          <div className="card">
            <label className="label">Version name</label>
            <input className="input" value={versionName} onChange={(e) => setVersionName(e.target.value)} />
          </div>

          <div className="card">
            <h2 className="font-semibold mb-2">Summary</h2>
            <textarea
              className="input min-h-[90px]"
              value={content.summary ?? ""}
              onChange={(e) => setContent({ ...content, summary: e.target.value })}
            />
          </div>

          <div className="card">
            <h2 className="font-semibold mb-2">Skills</h2>
            <input
              className="input"
              value={(content.skills ?? []).join(", ")}
              onChange={(e) => setContent({ ...content, skills: e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean) })}
            />
          </div>

          {["experience", "projects"].map((section) => (
            <div className="card" key={section}>
              <h2 className="font-semibold mb-3 capitalize">{section}</h2>
              <div className="space-y-4">
                {(content[section] ?? []).map((item: any, itemIndex: number) => (
                  <div key={itemIndex} className="border border-border rounded-lg p-3">
                    <div className="font-medium text-sm">{item.title || item.name}{item.company ? `, ${item.company}` : ""}</div>
                    <div className="space-y-2 mt-2">
                      {(item.bullets ?? []).map((bullet: string, bulletIndex: number) => {
                        const key = `${section}-${itemIndex}-${bulletIndex}`;
                        return (
                          <div key={bulletIndex}>
                            <textarea
                              className="input min-h-[50px] text-sm"
                              value={bullet}
                              onChange={(e) => updateBullet(section as any, itemIndex, bulletIndex, e.target.value)}
                            />
                            <div className="flex flex-wrap gap-1.5 mt-1.5">
                              {IMPROVE_MODES.map((m) => (
                                <button
                                  key={m.value}
                                  disabled={improvingKey === key}
                                  onClick={() => handleImprove(section as any, itemIndex, bulletIndex, m.value)}
                                  className="text-xs px-2 py-1 rounded-md border border-border text-ink-muted hover:bg-bg hover:text-ink flex items-center gap-1 disabled:opacity-50"
                                >
                                  <Wand2 className="w-3 h-3" /> {improvingKey === key ? "..." : m.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Live preview */}
        <div className="lg:sticky lg:top-6 h-fit">
          <div className="card !p-0 overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center gap-2 text-sm text-ink-muted">
              <Sparkles className="w-3.5 h-3.5" /> Live preview
            </div>
            <div className="p-6 max-h-[calc(100vh-160px)] overflow-y-auto">
              <ResumePreview content={content} />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function ResumePreview({ content }: { content: any }) {
  const personal = content.personal_information ?? {};
  return (
    <div className="text-sm space-y-4">
      <div>
        <h1 className="text-xl font-bold text-primary-900">{personal.full_name}</h1>
        {personal.headline && <p className="text-ink-muted">{personal.headline}</p>}
        <p className="text-xs text-ink-muted mt-1">
          {[personal.email, personal.phone, personal.location].filter(Boolean).join(" · ")}
        </p>
      </div>

      {content.summary && (
        <div>
          <h2 className="text-xs font-semibold uppercase text-primary-900 border-b border-primary-600 pb-1 mb-1.5">Summary</h2>
          <p className="text-ink-muted">{content.summary}</p>
        </div>
      )}

      {content.skills?.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold uppercase text-primary-900 border-b border-primary-600 pb-1 mb-1.5">Skills</h2>
          <div className="flex flex-wrap gap-1.5">
            {content.skills.map((s: string, i: number) => (
              <span key={i} className="badge-neutral">{s}</span>
            ))}
          </div>
        </div>
      )}

      {content.experience?.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold uppercase text-primary-900 border-b border-primary-600 pb-1 mb-1.5">Experience</h2>
          {content.experience.map((e: any, i: number) => (
            <div key={i} className="mb-3">
              <div className="font-medium">{e.title}, {e.company}</div>
              <ul className="list-disc list-inside text-ink-muted mt-1">
                {e.bullets?.map((b: string, bi: number) => <li key={bi}>{b}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}

      {content.projects?.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold uppercase text-primary-900 border-b border-primary-600 pb-1 mb-1.5">Projects</h2>
          {content.projects.map((p: any, i: number) => (
            <div key={i} className="mb-3">
              <div className="font-medium">{p.name}</div>
              <ul className="list-disc list-inside text-ink-muted mt-1">
                {p.bullets?.map((b: string, bi: number) => <li key={bi}>{b}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}

      {content.education?.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold uppercase text-primary-900 border-b border-primary-600 pb-1 mb-1.5">Education</h2>
          {content.education.map((ed: any, i: number) => (
            <div key={i} className="mb-1.5">
              <div className="font-medium">{ed.degree}{ed.field_of_study ? `, ${ed.field_of_study}` : ""}</div>
              <div className="text-ink-muted">{ed.institution}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
