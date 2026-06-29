import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { Activity, GitMerge, Plug, LogOut, Sparkles, Bell, Radio } from "lucide-react";

const NAV_ITEMS = [
  { label: "Overview", path: "/dashboard", icon: Activity, testId: "nav-overview" },
  { label: "Live", path: "/live", icon: Radio, testId: "nav-live" },
  { label: "Runs", path: "/runs", icon: GitMerge, testId: "nav-runs" },
  { label: "Insights", path: "/insights", icon: Sparkles, testId: "nav-insights" },
  { label: "Alerts", path: "/alerts", icon: Bell, testId: "nav-alerts" },
  { label: "Integrations", path: "/integrations", icon: Plug, testId: "nav-integrations" },
];

export function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-4 z-50 px-4" data-testid="app-header">
      <div className="max-w-7xl mx-auto">
        <div className="glass-nav rounded-2xl px-4 sm:px-6 py-2.5 flex items-center justify-between">
          {/* Left: Logo + Org */}
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="hover:opacity-80 transition-opacity flex items-center gap-2" data-testid="header-logo-link">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <Activity size={18} className="text-white" strokeWidth={2.5} />
              </div>
              <span className="font-display font-bold text-lg text-slate-900 tracking-tight">pipelynx</span>
            </Link>
            <div className="hidden md:flex items-center gap-2 pl-4 border-l border-slate-200">
              <span className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">Org</span>
              <span className="font-mono text-xs text-slate-700" data-testid="header-org-name">
                {user?.email?.split("@")[1] || "—"}
              </span>
            </div>
          </div>

          {/* Center: Navigation */}
          <nav className="hidden md:flex items-center gap-1" data-testid="primary-nav">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path
                || (item.path !== "/" && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={item.testId}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5",
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                  )}
                >
                  <Icon size={13} strokeWidth={2} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: User + Logout */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-white/60 border border-slate-200">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-xs">
                {user?.email?.[0]?.toUpperCase() || "?"}
              </div>
              <div className="hidden lg:block leading-tight">
                <div className="text-xs font-semibold text-slate-900" data-testid="header-user-name">
                  {user?.full_name || user?.email}
                </div>
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
                  {user?.role || "member"}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-full hover:bg-rose-50 transition-colors text-slate-500 hover:text-rose-600"
              title="Sign out"
              data-testid="logout-button"
            >
              <LogOut size={14} strokeWidth={2} />
            </button>
          </div>
        </div>

        {/* Mobile nav row */}
        <nav className="flex md:hidden mt-2 glass-card rounded-2xl px-2 py-2 gap-1 overflow-x-auto" data-testid="mobile-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap",
                  isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600"
                )}
              >
                <Icon size={12} strokeWidth={2} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

export function AppShell({ children }) {
  return (
    <div className="public-theme min-h-screen flex flex-col relative overflow-hidden" data-testid="app-shell">
      {/* Decorative floating orbs */}
      <div className="orb orb-blue w-96 h-96 -top-32 -left-32 opacity-40" style={{ animationDelay: "0s" }} />
      <div className="orb orb-violet w-80 h-80 top-1/2 -right-32 opacity-30" style={{ animationDelay: "2s" }} />

      <AppHeader />
      <main className="flex-1 relative z-10 pt-6 animate-fade-in">{children}</main>
      <footer className="mt-12 px-4 pb-6 relative z-10">
        <div className="max-w-7xl mx-auto glass-card rounded-2xl px-6 py-4 flex items-center justify-between text-xs text-slate-500">
          <div className="font-mono">PIPELYNX · v1.0.0 · Sparkcurv Technologies</div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-status-pulse" />
            <span className="uppercase tracking-wider text-[10px]">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
