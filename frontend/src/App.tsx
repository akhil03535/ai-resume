import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { ToastProvider } from "@/components/Toast";
import ProtectedRoute from "@/components/ProtectedRoute";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Upload from "@/pages/Upload";
import Profile from "@/pages/Profile";
import JobDescription from "@/pages/JobDescription";
import Analysis from "@/pages/Analysis";
import Generator from "@/pages/Generator";
import Editor from "@/pages/Editor";
import History from "@/pages/History";
import Settings from "@/pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/jobs" element={<ProtectedRoute><JobDescription /></ProtectedRoute>} />
              <Route path="/analysis/:jdId" element={<ProtectedRoute><Analysis /></ProtectedRoute>} />
              <Route path="/generator" element={<ProtectedRoute><Generator /></ProtectedRoute>} />
              <Route path="/editor/:resumeId" element={<ProtectedRoute><Editor /></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
