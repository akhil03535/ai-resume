import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-8 h-8 rounded-md bg-primary-900 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">ResumeAI</span>
        </div>
        <div className="card">
          <h1 className="text-xl font-semibold text-ink">Welcome back</h1>
          <p className="text-sm text-ink-muted mt-1 mb-6">Log in to continue building your resume.</p>
          {error && <div className="mb-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg p-3">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="email">Email</label>
              <input id="email" type="email" required className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="password">Password</label>
              <input id="password" type="password" required className="input" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Logging in..." : "Log in"}
            </button>
          </form>
        </div>
        <p className="text-center text-sm text-ink-muted mt-4">
          Don't have an account? <Link to="/register" className="text-primary-700 font-medium">Register</Link>
        </p>
      </div>
    </div>
  );
}
