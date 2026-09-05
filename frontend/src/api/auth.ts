import { api, setTokens } from "./client";
import type { User } from "@/types";

export async function register(email: string, password: string, full_name: string) {
  const { data } = await api.post("/api/auth/register", { email, password, full_name });
  setTokens(data);
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/api/auth/login", { email, password });
  setTokens(data);
  return data;
}

export function logout() {
  setTokens(null);
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get("/api/auth/me");
  return data;
}
