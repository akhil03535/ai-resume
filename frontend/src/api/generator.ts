import { api } from "./client";
import type { GeneratedResume, ResumeTemplate } from "@/types";

export async function listTemplates(): Promise<ResumeTemplate[]> {
  const { data } = await api.get("/api/generator/templates");
  return data;
}

export async function generateResume(payload: {
  job_description_id: string;
  template_slug: string;
  version_name: string;
  target_role?: string;
  target_company?: string;
  sections?: string[];
}): Promise<GeneratedResume> {
  const { data } = await api.post("/api/generator/generate", payload);
  return data;
}

export async function listGeneratedResumes(): Promise<GeneratedResume[]> {
  const { data } = await api.get("/api/generator/resumes");
  return data;
}

export async function getGeneratedResume(id: string): Promise<GeneratedResume> {
  const { data } = await api.get(`/api/generator/resumes/${id}`);
  return data;
}

export async function updateGeneratedResume(id: string, content: any, version_name?: string): Promise<GeneratedResume> {
  const { data } = await api.put(`/api/generator/resumes/${id}`, { content, version_name });
  return data;
}

export async function reanalyzeGeneratedResume(id: string): Promise<GeneratedResume> {
  const { data } = await api.post(`/api/generator/resumes/${id}/reanalyze`);
  return data;
}

export async function duplicateGeneratedResume(id: string, new_name: string): Promise<GeneratedResume> {
  const { data } = await api.post(`/api/generator/resumes/${id}/duplicate`, null, { params: { new_name } });
  return data;
}

export async function renameGeneratedResume(id: string, new_name: string): Promise<GeneratedResume> {
  const { data } = await api.put(`/api/generator/resumes/${id}/rename`, null, { params: { new_name } });
  return data;
}

export async function deleteGeneratedResume(id: string): Promise<void> {
  await api.delete(`/api/generator/resumes/${id}`);
}

export async function improveBullet(text: string, mode: string, context?: string): Promise<{ improved_text: string; notes: string | null }> {
  const { data } = await api.post("/api/generator/improve-bullet", { text, mode, context });
  return data;
}

export function exportPdfUrl(id: string) {
  return `/api/generator/resumes/${id}/export/pdf`;
}

export function exportDocxUrl(id: string) {
  return `/api/generator/resumes/${id}/export/docx`;
}
