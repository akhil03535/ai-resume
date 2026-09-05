import { api } from "./client";
import type { ResumeFile } from "@/types";

export async function uploadResume(file: File): Promise<ResumeFile> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/resumes/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function parseResume(resumeId: string) {
  const { data } = await api.post(`/api/resumes/${resumeId}/parse`);
  return data;
}

export async function listResumes(): Promise<ResumeFile[]> {
  const { data } = await api.get("/api/resumes");
  return data;
}
