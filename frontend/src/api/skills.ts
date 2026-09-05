import { api } from "./client";
import type { MissingSkillPrompt } from "@/types";

export async function getMissingSkills(analysisId: string): Promise<MissingSkillPrompt[]> {
  const { data } = await api.get(`/api/skills/analyses/${analysisId}/missing`);
  return data;
}

export interface VerifyPayload {
  skill_name: string;
  answer: "yes" | "basic" | "no";
  evidence?: { source_type: string; description: string }[];
}

export async function verifySkill(payload: VerifyPayload) {
  const { data } = await api.post("/api/skills/verify", payload);
  return data;
}
