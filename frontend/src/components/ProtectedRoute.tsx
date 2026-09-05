import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";
import { LoadingState } from "@/components/States";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <LoadingState message="Loading..." />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
