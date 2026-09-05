import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  User as UserIcon,
  FileText,
  BarChart3,
  Sparkles,
  History,
  Settings,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload Resume", icon: Upload },
  { to: "/profile", label: "Candidate Profile", icon: UserIcon },
  { to: "/jobs", label: "Job Description", icon: FileText },
  { to: "/generator", label: "Generator", icon: Sparkles },
  { to: "/history", label: "Resume History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex bg-bg">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 border-r border-border bg-white">
        <div className="h-16 flex items-center gap-2 px-6 border-b border-border">
          <div className="w-7 h-7 rounded-md bg-primary-900 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-ink tracking-tight">ResumeAI</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map((item) => (
            <SidebarLink key={item.to} {...item} />
          ))}
        </nav>
        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg mb-1">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-900 flex items-center justify-center text-sm font-semibold">
              {user?.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">{user?.full_name}</div>
              <div className="text-xs text-ink-muted truncate">{user?.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="btn-ghost w-full justify-start">
            <LogOut className="w-4 h-4" /> Log out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header className="lg:hidden h-14 flex items-center justify-between px-4 border-b border-border bg-white sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary-900 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-semibold text-sm">ResumeAI</span>
          </div>
          <button onClick={() => setDrawerOpen(true)} aria-label="Open menu" className="p-2 -mr-2">
            <Menu className="w-5 h-5" />
          </button>
        </header>

        {/* Mobile drawer */}
        {drawerOpen && (
          <div className="lg:hidden fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/30" onClick={() => setDrawerOpen(false)} />
            <div className="absolute right-0 top-0 h-full w-72 bg-white shadow-xl p-4 animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <span className="font-semibold">Menu</span>
                <button onClick={() => setDrawerOpen(false)} aria-label="Close menu" className="p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <nav className="space-y-0.5">
                {NAV_ITEMS.map((item) => (
                  <SidebarLink key={item.to} {...item} onClick={() => setDrawerOpen(false)} />
                ))}
              </nav>
              <button onClick={handleLogout} className="btn-ghost w-full justify-start mt-4">
                <LogOut className="w-4 h-4" /> Log out
              </button>
            </div>
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}

function SidebarLink({
  to,
  label,
  icon: Icon,
  onClick,
}: {
  to: string;
  label: string;
  icon: any;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
          isActive ? "bg-primary-50 text-primary-900" : "text-ink-muted hover:bg-bg hover:text-ink"
        )
      }
    >
      <Icon className="w-4 h-4" />
      {label}
    </NavLink>
  );
}
