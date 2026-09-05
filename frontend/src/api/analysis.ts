import { api } from "./client";
import type { ResumeAnalysis } from "@/types";

export async function runAnalysis(payload: { job_description_id: string; resume_id?: string; generated_resume_id?: string }): Promise<ResumeAnalysis> {
  const { data } = await api.post("/api/analysis/run", payload);
  return data;
}

export async function getAnalysis(id: string): Promise<ResumeAnalysis> {
  const { data } = await api.get(`/api/analysis/${id}`);
  return data;
}

export async function listAnalysesForJob(jdId: string): Promise<ResumeAnalysis[]> {
  const { data } = await api.get(`/api/analysis/by-job/${jdId}`);
  return data;
}
