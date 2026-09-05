import { api } from "./client";
import type { CandidateProfile } from "@/types";

export async function getProfile(): Promise<CandidateProfile> {
  const { data } = await api.get("/api/profile");
  return data;
}

export async function updateProfile(payload: Partial<CandidateProfile> & { skill_names?: string[] }): Promise<CandidateProfile> {
  const { data } = await api.put("/api/profile", payload);
  return data;
}
