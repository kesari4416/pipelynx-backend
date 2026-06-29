import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, Sparkles, Bell, GitMerge, ShieldCheck, Plug, TrendingUp,
  Zap, CheckCircle2, Activity, Cloud,
} from "lucide-react";
import {
  SiGithubactions, SiGitlab, SiJenkins, SiArgo, SiCircleci, SiBitbucket,
} from "react-icons/si";

const INTEGRATIONS = [
  { name: "GitHub Actions", Icon: SiGithubactions, color: "#2088FF" },
  { name: "GitLab CI", Icon: SiGitlab, color: "#FC6D26" },
  { name: "Jenkins", Icon: SiJenkins, color: "#D33833" },
  { name: "ArgoCD", Icon: SiArgo, color: "#EF7B4D" },
  { name: "CircleCI", Icon: SiCircleci, color: "#161616" },
  { name: "AWS CodePipeline", Icon: Cloud, color: "#FF9900" },
  { name: "Bitbucket", Icon: SiBitbucket, color: "#2684FF" },
];

const FEATURES = [
  { icon: GitMerge, title: "Unified pipeline view", body: "One inbox for every CI/CD run across 7 platforms. No more tab-switching." },
  { icon: TrendingUp, title: "DORA metrics, automatic", body: "Deployment Frequency, Lead Time, Change Failure Rate, MTTR — calculated continuously." },
  { icon: Sparkles, title: "AI failure analysis", body: "GPT-class root-cause analysis on every failed run. Cross-pipeline pattern detection." },
  { icon: Bell, title: "Smart alerting", body: "Rules engine routes alerts to Slack, Email, or webhook. Anomaly detection flags issues early." },
  { icon: ShieldCheck, title: "Multi-tenant security", body: "Organization-scoped isolation. JWT auth, audit-ready logs, SOC 2-ready architecture." },
  { icon: Plug, title: "Setup in 5 minutes", body: "Paste a webhook URL. We handle parsing, normalization, and dashboards from there." },
];

const STEPS = [
  { n: "01", title: "Connect a webhook", body: "Pick a CI/CD platform, paste our webhook URL into its settings. Done." },
  { n: "02", title: "Pipelynx normalizes", body: "We parse every webhook into a unified PipelineRun schema, regardless of source." },
  { n: "03", title: "Dashboards light up", body: "Runs, metrics, and AI insights populate within seconds. No SQL, no setup." },
  { n: "04", title: "Alerts when it matters", body: "Define rules, get notified on failures, slowdowns, or anomalies. Sleep better." },
];

const TESTIMONIALS = [
  { quote: "We cut our mean-time-to-recovery by 38% in the first quarter. The AI summaries point us at the root cause within minutes.", name: "Anika R.", role: "Platform Lead", org: "Series-B Fintech", initials: "AR" },
  { quote: "Before Pipelynx we had three tabs open across Jenkins, Argo, and GitHub. Now I have one. That's the whole pitch.", name: "Marco T.", role: "Staff SRE", org: "Healthcare SaaS", initials: "MT" },
  { quote: "DORA metrics from day one without writing a single query. My VPE finally has the data she's been asking for.", name: "Priya K.", role: "Engineering Manager", org: "Logistics Platform", initials: "PK" },
];

const FAQS = [
  { q: "How long does setup take?", a: "5 minutes for the first integration. Paste our webhook URL into your CI/CD platform's settings and we'll start ingesting events immediately." },
  { q: "Which platforms are supported?", a: "GitHub Actions, GitLab CI, Jenkins, ArgoCD, CircleCI, AWS CodePipeline, and Bitbucket Pipelines. Custom webhooks on Enterprise." },
  { q: "Is there a free plan?", a: "Yes — Free includes 1,000 pipeline runs/month, 3 integrations, and full DORA metrics. No credit card required." },
  { q: "What about data privacy?", a: "Your pipeline metadata stays in your dedicated organization namespace. Enterprise customers can deploy in their own VPC." },
];

function SectionTag({ children }) {
  return <div className="pill-badge font-body">{children}</div>;
}

export function LandingPage() {
  return (
    <div data-testid="landing-page" className="font-body">
      {/* ============ Hero ============ */}
      <section className="relative px-4 pt-12 pb-20 sm:pt-20 sm:pb-28">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center justify-center mb-8">
            <SectionTag>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-status-pulse" />
              v1.0 · live now
            </SectionTag>
          </div>
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] mb-6 text-slate-900" data-testid="hero-heading">
            Every build. Every deploy.<br />
            <span className="gradient-text">One signal source.</span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed mb-10">
            Pipelynx unifies GitHub Actions, GitLab, Jenkins, ArgoCD, CircleCI,
            AWS, and Bitbucket into a single command center. Track DORA metrics,
            surface failure patterns with AI, ship faster.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link to="/auth/register" className="btn-gradient inline-flex items-center gap-2 rounded-full px-7 py-3.5 text-sm font-semibold" data-testid="hero-cta-primary">
              Get started free <ArrowRight size={16} />
            </Link>
            <Link to="/pricing" className="btn-glass inline-flex items-center gap-2 rounded-full px-7 py-3.5 text-sm font-semibold" data-testid="hero-cta-secondary">
              See pricing <ArrowRight size={16} />
            </Link>
          </div>
          <div className="mt-6 text-xs text-slate-500 font-medium">No credit card · 5-min setup</div>

          {/* Metric tiles */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto" data-testid="hero-metrics">
            {[
              { v: "7", l: "CI/CD platforms" },
              { v: "DORA", l: "Out of the box" },
              { v: "99.9%", l: "Uptime SLA" },
              { v: "5min", l: "Setup time" },
            ].map((t) => (
              <div key={t.l} className="glass-card rounded-2xl p-6 lift-on-hover">
                <div className="font-display text-3xl font-bold text-slate-900 mb-1">{t.v}</div>
                <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">{t.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ Integrations strip ============ */}
      <section className="px-4 mb-20" data-testid="integrations-strip">
        <div className="max-w-6xl mx-auto">
          <div className="glass-card rounded-3xl p-8 sm:p-10">
            <div className="text-center mb-8">
              <SectionTag>Integrates with</SectionTag>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-4">
              {INTEGRATIONS.map(({ name, Icon, color }) => (
                <div
                  key={name}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl hover:bg-white/60 transition-colors group"
                  data-testid={`integration-${name.toLowerCase().replace(/\s+/g, "-")}`}
                >
                  <Icon size={32} style={{ color }} className="group-hover:scale-110 transition-transform" />
                  <span className="text-xs text-slate-600 font-medium text-center leading-tight">{name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ Features bento ============ */}
      <section className="px-4 py-16" data-testid="features-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <SectionTag>Capabilities</SectionTag>
            <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mt-4 mb-4">
              The control plane for<br />
              <span className="gradient-text">your delivery pipeline.</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Six interlocking primitives that turn raw CI/CD events into engineering leverage.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.title}
                  className="glass-card rounded-3xl p-7 lift-on-hover"
                  data-testid={`feature-${feat.title.toLowerCase().replace(/[^a-z]+/g, "-")}`}
                >
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-5 shadow-lg shadow-indigo-500/30">
                    <Icon size={22} className="text-white" strokeWidth={2} />
                  </div>
                  <h3 className="font-display text-xl font-bold text-slate-900 mb-2">{feat.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{feat.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============ How it works ============ */}
      <section className="px-4 py-16" data-testid="how-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <SectionTag>How it works</SectionTag>
            <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mt-4">
              Four steps to a unified<br />
              <span className="gradient-text">pipeline observability layer.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {STEPS.map((step) => (
              <div key={step.n} className="glass-card rounded-3xl p-7 lift-on-hover" data-testid={`step-${step.n}`}>
                <div className="font-display text-5xl font-bold gradient-text mb-4">{step.n}</div>
                <h3 className="font-display text-lg font-bold text-slate-900 mb-2">{step.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ Testimonials ============ */}
      <section className="px-4 py-16" data-testid="testimonials-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <SectionTag>What teams say</SectionTag>
            <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mt-4">
              Trusted by teams that<br />
              <span className="gradient-text">ship every day.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t) => (
              <figure key={t.name} className="glass-card rounded-3xl p-7 lift-on-hover flex flex-col" data-testid={`testimonial-${t.name.split(" ")[0].toLowerCase()}`}>
                <div className="flex gap-0.5 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Zap key={i} size={14} className="text-amber-400 fill-amber-400" />
                  ))}
                </div>
                <blockquote className="text-base text-slate-700 leading-relaxed flex-1 mb-6">"{t.quote}"</blockquote>
                <figcaption className="flex items-center gap-3 pt-5 border-t border-slate-200">
                  <div className="w-11 h-11 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                    {t.initials}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{t.name}</div>
                    <div className="text-xs text-slate-500">{t.role} · {t.org}</div>
                  </div>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* ============ FAQ ============ */}
      <section className="px-4 py-16" data-testid="faq-section">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <SectionTag>FAQ</SectionTag>
            <h2 className="font-display text-4xl font-bold tracking-tight mt-4">Common questions</h2>
          </div>
          <div className="space-y-3">
            {FAQS.map((item, idx) => (
              <details
                key={item.q}
                className="group glass-card rounded-2xl px-6 py-5"
                data-testid={`faq-${idx}`}
              >
                <summary className="cursor-pointer flex items-center justify-between list-none">
                  <span className="text-base font-semibold text-slate-900">{item.q}</span>
                  <span className="w-7 h-7 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl font-light group-open:rotate-45 transition-transform">+</span>
                </summary>
                <p className="mt-4 text-sm text-slate-600 leading-relaxed pr-10">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ============ CTA ============ */}
      <section className="px-4 py-20" data-testid="landing-cta-section">
        <div className="max-w-5xl mx-auto">
          <div className="relative glass-card-strong rounded-3xl p-12 sm:p-16 text-center overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none" />
            <div className="relative z-10">
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/40">
                <Activity size={28} className="text-white" strokeWidth={2} />
              </div>
              <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mb-4 text-slate-900">
                Ready to see every pipeline<br />
                <span className="gradient-text">in one place?</span>
              </h2>
              <p className="text-lg text-slate-600 mb-8 max-w-xl mx-auto">
                14-day free trial on paid plans. No credit card. No call required.
              </p>
              <div className="flex items-center justify-center gap-3 flex-wrap">
                <Link to="/auth/register" className="btn-gradient inline-flex items-center gap-2 rounded-full px-8 py-4 text-sm font-semibold" data-testid="landing-cta-primary">
                  Start free <ArrowRight size={16} />
                </Link>
                <Link to="/pricing" className="btn-glass inline-flex items-center gap-2 rounded-full px-8 py-4 text-sm font-semibold" data-testid="landing-cta-secondary">
                  See pricing
                </Link>
              </div>
              <div className="mt-8 flex items-center justify-center gap-6 text-sm text-slate-500">
                <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-emerald-500" /> No credit card</span>
                <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-emerald-500" /> Cancel anytime</span>
                <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-emerald-500" /> 5-min setup</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default LandingPage;
