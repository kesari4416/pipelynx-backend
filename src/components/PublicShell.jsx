import React, { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { ArrowRight, Menu, X, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const PUBLIC_NAV = [
  { label: "Home", path: "/", testId: "public-nav-home" },
  { label: "About", path: "/about", testId: "public-nav-about" },
  { label: "Blog", path: "/blog", testId: "public-nav-blog" },
  { label: "Pricing", path: "/pricing", testId: "public-nav-pricing" },
];

function NavItem({ item, onClick }) {
  return (
    <NavLink
      to={item.path}
      end={item.path === "/"}
      onClick={onClick}
      data-testid={item.testId}
      className={({ isActive }) =>
        cn(
          "px-4 py-2 rounded-full text-sm font-medium transition-all",
          isActive
            ? "bg-indigo-50 text-indigo-700"
            : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
        )
      }
    >
      {item.label}
    </NavLink>
  );
}

export function PublicHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-4 z-50 px-4" data-testid="public-header">
      <div className="max-w-6xl mx-auto">
        <div className="glass-nav rounded-2xl px-4 sm:px-6 py-2.5 flex items-center justify-between">
          <Link to="/" className="hover:opacity-80 transition-opacity flex items-center gap-2" data-testid="public-header-logo">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Activity size={18} className="text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display font-bold text-lg text-slate-900 tracking-tight">pipelynx</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1" data-testid="public-desktop-nav">
            {PUBLIC_NAV.map((item) => (
              <NavItem key={item.path} item={item} />
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center gap-2">
            <Link
              to="/auth/login"
              data-testid="public-signin-link"
              className="text-sm font-medium text-slate-700 hover:text-slate-900 px-3 py-2 transition-colors"
            >
              Sign in
            </Link>
            <Link
              to="/auth/register"
              data-testid="public-getstarted-link"
              className="btn-gradient inline-flex items-center gap-1.5 rounded-full px-5 py-2 text-sm font-semibold"
            >
              Get started
              <ArrowRight size={14} strokeWidth={2.5} />
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 text-slate-600 hover:text-slate-900"
            onClick={() => setMobileOpen((v) => !v)}
            data-testid="public-mobile-toggle"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden mt-2 glass-card-strong rounded-2xl p-4 flex flex-col gap-1" data-testid="public-mobile-nav">
            {PUBLIC_NAV.map((item) => (
              <NavItem key={item.path} item={item} onClick={() => setMobileOpen(false)} />
            ))}
            <div className="flex items-center gap-2 pt-3 mt-2 border-t border-slate-200">
              <Link
                to="/auth/login"
                onClick={() => setMobileOpen(false)}
                className="flex-1 text-center text-sm font-medium text-slate-700 hover:text-slate-900 px-3 py-2.5 rounded-full border border-slate-200"
              >
                Sign in
              </Link>
              <Link
                to="/auth/register"
                onClick={() => setMobileOpen(false)}
                className="btn-gradient flex-1 text-center px-3 py-2.5 rounded-full text-sm font-semibold"
              >
                Get started
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="mt-24 px-4 pb-8" data-testid="public-footer">
      <div className="max-w-6xl mx-auto glass-card rounded-3xl p-10 md:p-14">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <Activity size={20} className="text-white" strokeWidth={2.5} />
              </div>
              <span className="font-display font-bold text-xl text-slate-900">pipelynx</span>
            </div>
            <p className="text-sm text-slate-600 max-w-sm leading-relaxed">
              Pipeline intelligence for engineering teams. Unify 7 CI/CD platforms,
              track DORA metrics, ship faster.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold tracking-widest uppercase text-slate-400 mb-4">Product</div>
            <ul className="space-y-3 text-sm">
              <li><Link to="/pricing" className="text-slate-600 hover:text-indigo-600 transition-colors">Pricing</Link></li>
              <li><Link to="/auth/register" className="text-slate-600 hover:text-indigo-600 transition-colors">Get started</Link></li>
              <li><Link to="/auth/login" className="text-slate-600 hover:text-indigo-600 transition-colors">Sign in</Link></li>
            </ul>
          </div>
          <div>
            <div className="text-xs font-semibold tracking-widest uppercase text-slate-400 mb-4">Company</div>
            <ul className="space-y-3 text-sm">
              <li><Link to="/about" className="text-slate-600 hover:text-indigo-600 transition-colors">About us</Link></li>
              <li><Link to="/blog" className="text-slate-600 hover:text-indigo-600 transition-colors">Blog</Link></li>
              <li><a href="mailto:hello@pipelynx.io" className="text-slate-600 hover:text-indigo-600 transition-colors">Contact</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-200 pt-6 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <div>© Sparkcurv Technologies Pvt. Ltd. · Nagercoil, Tamil Nadu</div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-status-pulse" />
            <span className="font-medium">All Systems Operational</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function PublicShell({ children }) {
  return (
    <div className="public-theme min-h-screen flex flex-col relative overflow-hidden" data-testid="public-shell">
      {/* Decorative floating orbs */}
      <div className="orb orb-blue w-96 h-96 -top-32 -left-32" style={{ animationDelay: "0s" }} />
      <div className="orb orb-violet w-80 h-80 top-1/3 -right-32" style={{ animationDelay: "2s" }} />
      <div className="orb orb-pink w-72 h-72 bottom-1/4 left-1/4 opacity-30" style={{ animationDelay: "4s" }} />

      <PublicHeader />
      <main className="flex-1 relative z-10 pt-8 animate-fade-in">{children}</main>
      <PublicFooter />
    </div>
  );
}
