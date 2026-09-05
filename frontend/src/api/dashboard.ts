import { api } from "./client";
import type { DashboardData } from "@/types";

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await api.get("/api/dashboard");
  return data;
}
