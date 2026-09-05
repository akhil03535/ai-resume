import { api } from "./client";
import type { JobDescription } from "@/types";

export async function createJobDescription(payload: { title: string; company_name?: string; raw_text: string }): Promise<JobDescription> {
  const { data } = await api.post("/api/jobs", payload);
  return data;
}

export async function analyzeJobDescription(id: string): Promise<JobDescription> {
  const { data } = await api.post(`/api/jobs/${id}/analyze`);
  return data;
}

export async function listJobDescriptions(): Promise<JobDescription[]> {
  const { data } = await api.get("/api/jobs");
  return data;
}

export async function getJobDescription(id: string): Promise<JobDescription> {
  const { data } = await api.get(`/api/jobs/${id}`);
  return data;
}
