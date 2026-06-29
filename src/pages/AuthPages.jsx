import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ArrowRight, Loader2, Activity, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Shared split-screen auth layout with light glass aesthetic.
 * Left: gradient brand panel · Right: glass form card.
 */
function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="public-theme min-h-screen flex relative overflow-hidden" data-testid="auth-layout">
      {/* Floating orbs */}
      <div className="orb orb-blue w-96 h-96 -top-32 -left-32" style={{ animationDelay: "0s" }} />
      <div className="orb orb-violet w-80 h-80 top-1/3 -right-32" style={{ animationDelay: "2s" }} />
      <div className="orb orb-pink w-72 h-72 bottom-1/4 left-1/4 opacity-25" style={{ animationDelay: "4s" }} />

      {/* Left: brand panel */}
      <div className="hidden lg:flex lg:w-1/2 relative z-10 flex-col justify-between p-12">
        <Link to="/" className="inline-flex items-center gap-2 hover:opacity-80 transition-opacity w-fit">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Activity size={22} className="text-white" strokeWidth={2.5} />
          </div>
          <span className="font-display font-bold text-2xl text-slate-900 tracking-tight">pipelynx</span>
        </Link>

        <div className="max-w-lg">
          <div className="pill-badge font-body mb-5">Pipeline Intelligence</div>
          <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight leading-[1.05] mb-5 text-slate-900">
            Every build, every deploy.<br />
            <span className="gradient-text">One signal source.</span>
          </h2>
          <p className="text-base text-slate-600 leading-relaxed mb-10">
            Unify GitHub Actions, GitLab, Jenkins, CircleCI, ArgoCD, AWS, and Bitbucket
            into a single command center. Track DORA metrics, detect anomalies, ship faster.
          </p>
          <div className="grid grid-cols-3 gap-3 max-w-md">
            {[
              { v: "7", l: "Integrations" },
              { v: "DORA", l: "Metrics" },
              { v: "99.9%", l: "Uptime SLA" },
            ].map((t) => (
              <div key={t.l} className="glass-card rounded-2xl p-4">
                <div className="font-display text-2xl font-bold gradient-text">{t.v}</div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mt-1">{t.l}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="text-xs text-slate-500 font-mono">
          © Sparkcurv Technologies · Nagercoil
        </div>
      </div>

      {/* Right: form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 relative z-10">
        <div className="w-full max-w-md">
          <Link
            to="/"
            className="lg:hidden inline-flex items-center gap-2 hover:opacity-80 transition-opacity mb-10"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Activity size={20} className="text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display font-bold text-xl text-slate-900">pipelynx</span>
          </Link>

          <div className="glass-card-strong rounded-3xl p-8 sm:p-10">
            <div className="mb-8">
              <div className="text-xs uppercase tracking-widest text-indigo-600 font-bold mb-2">{subtitle}</div>
              <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
            </div>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

function Input({ label, error, ...props }) {
  return (
    <div className="mb-4">
      <label className="block text-xs uppercase tracking-widest text-slate-600 font-bold mb-2">{label}</label>
      <input
        {...props}
        className={cn(
          "w-full bg-white/80 backdrop-blur-md border rounded-xl px-4 py-3 text-sm text-slate-900",
          "placeholder:text-slate-400 focus:outline-none focus:ring-2 transition-all",
          error
            ? "border-rose-300 focus:border-rose-400 focus:ring-rose-100"
            : "border-slate-200 focus:border-indigo-400 focus:ring-indigo-100",
        )}
      />
      {error && <div className="text-rose-600 text-xs mt-1 font-medium">{error}</div>}
    </div>
  );
}

function PrimaryButton({ children, loading, ...props }) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={cn(
        "btn-gradient w-full rounded-full px-5 py-3.5 text-sm font-bold uppercase tracking-wider",
        "inline-flex items-center justify-center gap-2",
        "disabled:opacity-60 disabled:cursor-not-allowed",
        props.className,
      )}
    >
      {loading ? (
        <>
          <Loader2 size={14} className="animate-spin" />
          Processing…
        </>
      ) : (
        <>
          {children}
          <ArrowRight size={14} />
        </>
      )}
    </button>
  );
}

function ErrorBanner({ children, testId }) {
  return (
    <div
      className="flex items-start gap-2 border border-rose-200 bg-rose-50 text-rose-700 text-xs font-medium rounded-xl px-3 py-2.5 mb-4"
      data-testid={testId}
    >
      <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
      <span>{children}</span>
    </div>
  );
}

// ============ Login Page ============
export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const from = location.state?.from || "/";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Sign in" subtitle="Welcome back">
      <form onSubmit={handleSubmit} className="space-y-1" data-testid="login-form">
        <Input
          label="Email address"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
          data-testid="login-email-input"
        />
        <Input
          label="Password"
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          data-testid="login-password-input"
        />
        {error && <ErrorBanner testId="login-error">{error}</ErrorBanner>}
        <PrimaryButton loading={loading} type="submit" data-testid="login-submit-button">
          Sign in
        </PrimaryButton>
      </form>
      <div className="mt-7 text-sm text-slate-500 text-center">
        Don't have an account?{" "}
        <Link
          to="/auth/register"
          className="font-semibold gradient-text hover:opacity-80"
          data-testid="login-to-register-link"
        >
          Create one →
        </Link>
      </div>
    </AuthLayout>
  );
}

// ============ Register Page ============
export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    organization_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field) => (e) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(formData);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create account" subtitle="Get started in 30 seconds">
      <form onSubmit={handleSubmit} className="space-y-1" data-testid="register-form">
        <Input
          label="Full name"
          type="text"
          required
          value={formData.full_name}
          onChange={handleChange("full_name")}
          placeholder="Jane Doe"
          data-testid="register-fullname-input"
        />
        <Input
          label="Organization name"
          type="text"
          required
          value={formData.organization_name}
          onChange={handleChange("organization_name")}
          placeholder="Acme Inc."
          data-testid="register-org-input"
        />
        <Input
          label="Work email"
          type="email"
          required
          autoComplete="email"
          value={formData.email}
          onChange={handleChange("email")}
          placeholder="jane@acme.com"
          data-testid="register-email-input"
        />
        <Input
          label="Password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={formData.password}
          onChange={handleChange("password")}
          placeholder="At least 8 characters"
          data-testid="register-password-input"
        />
        {error && <ErrorBanner testId="register-error">{error}</ErrorBanner>}
        <PrimaryButton loading={loading} type="submit" data-testid="register-submit-button">
          Create account
        </PrimaryButton>
      </form>
      <div className="mt-7 text-sm text-slate-500 text-center">
        Already have an account?{" "}
        <Link
          to="/auth/login"
          className="font-semibold gradient-text hover:opacity-80"
          data-testid="register-to-login-link"
        >
          Sign in →
        </Link>
      </div>
    </AuthLayout>
  );
}
