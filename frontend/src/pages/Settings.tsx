import { useAuth } from "@/hooks/useAuth";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";

export default function Settings() {
  const { user } = useAuth();

  return (
    <Layout>
      <PageHeader title="Settings" subtitle="Manage your account." />
      <div className="card max-w-lg">
        <h2 className="font-semibold mb-4">Account</h2>
        <div className="space-y-3 text-sm">
          <div>
            <div className="text-ink-muted">Full name</div>
            <div className="font-medium">{user?.full_name}</div>
          </div>
          <div>
            <div className="text-ink-muted">Email</div>
            <div className="font-medium">{user?.email}</div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
