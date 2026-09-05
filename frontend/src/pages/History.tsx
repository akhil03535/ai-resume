import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Copy, Download, Pencil, Trash2 } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { LoadingState, EmptyState } from "@/components/States";
import { useToast } from "@/components/Toast";
import {
  listGeneratedResumes,
  duplicateGeneratedResume,
  renameGeneratedResume,
  deleteGeneratedResume,
  exportPdfUrl,
} from "@/api/generator";
import { api, apiErrorMessage } from "@/api/client";

export default function History() {
  const { data, isLoading, refetch } = useQuery({ queryKey: ["generated-resumes"], queryFn: listGeneratedResumes });
  const { show } = useToast();
  const navigate = useNavigate();
  const [busyId, setBusyId] = useState<string | null>(null);

  async function handleDuplicate(id: string, name: string) {
    setBusyId(id);
    try {
      const copy = await duplicateGeneratedResume(id, `${name} (copy)`);
      show("success", "Resume duplicated.");
      refetch();
      navigate(`/editor/${copy.id}`);
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleRename(id: string, currentName: string) {
    const newName = window.prompt("Rename version", currentName);
    if (!newName || newName === currentName) return;
    setBusyId(id);
    try {
      await renameGeneratedResume(id, newName);
      show("success", "Renamed.");
      refetch();
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this resume version? This cannot be undone.")) return;
    setBusyId(id);
    try {
      await deleteGeneratedResume(id);
      show("success", "Deleted.");
      refetch();
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDownload(id: string, name: string) {
    try {
      const response = await api.get(exportPdfUrl(id), { responseType: "blob" });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${name}.pdf`;
      link.click();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      show("error", apiErrorMessage(err));
    }
  }

  return (
    <Layout>
      <PageHeader title="Resume History" subtitle="All your generated, tailored resume versions." />

      {isLoading && <LoadingState />}

      {data && data.length === 0 && (
        <EmptyState title="No generated resumes yet" description="Generate your first tailored resume to see it here." />
      )}

      {data && data.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((r) => (
            <div key={r.id} className="card flex flex-col">
              <button className="text-left flex-1" onClick={() => navigate(`/editor/${r.id}`)}>
                <h3 className="font-medium text-ink truncate">{r.version_name}</h3>
                <p className="text-xs text-ink-muted mt-1">{new Date(r.created_at).toLocaleDateString()}</p>
                <div className="flex gap-3 mt-3 text-sm">
                  <span>ATS <strong>{r.ats_score ?? "—"}</strong></span>
                  <span>Match <strong>{r.job_match_score ?? "—"}%</strong></span>
                </div>
              </button>
              <div className="flex gap-1 mt-3 pt-3 border-t border-border">
                <button disabled={busyId === r.id} title="Rename" className="btn-ghost !px-2" onClick={() => handleRename(r.id, r.version_name)}>
                  <Pencil className="w-4 h-4" />
                </button>
                <button disabled={busyId === r.id} title="Duplicate" className="btn-ghost !px-2" onClick={() => handleDuplicate(r.id, r.version_name)}>
                  <Copy className="w-4 h-4" />
                </button>
                <button title="Download PDF" className="btn-ghost !px-2" onClick={() => handleDownload(r.id, r.version_name)}>
                  <Download className="w-4 h-4" />
                </button>
                <button disabled={busyId === r.id} title="Delete" className="btn-ghost !px-2 text-danger ml-auto" onClick={() => handleDelete(r.id)}>
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
