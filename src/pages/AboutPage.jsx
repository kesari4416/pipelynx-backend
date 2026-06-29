import React from "react";
import { Link } from "react-router-dom";
import { Mail, MapPin, ArrowRight, Compass, Target, Lightbulb, Users } from "lucide-react";

const VALUES = [
  { icon: Compass, title: "Engineering-first", body: "We build for the engineers we used to be. No fluff dashboards, only the signals that change how teams ship." },
  { icon: Target, title: "Pragmatic over hype", body: "AI where it earns its keep, not where it looks good in a demo. DORA before dashboards. Webhooks before agents." },
  { icon: Lightbulb, title: "Open by default", body: "Our schemas, our integration list, and our roadmap are all public. We win when our customers can extend us." },
  { icon: Users, title: "Customer-funded", body: "We're built to last because we're built on revenue, not vibes. Every feature has a customer asking for it." },
];

const TEAM = [
  { initials: "AD", name: "Founder & CEO", role: "Vision · Platform · Strategy" },
  { initials: "ML", name: "Engineering", role: "Platform · Backend · DevOps" },
  { initials: "PR", name: "Product Design", role: "UX · Brand · Frontend" },
  { initials: "+", name: "We're hiring", role: "Open roles in Platform Engineering" },
];

const STATS = [
  { value: "2025", label: "Founded" },
  { value: "Nagercoil", label: "Headquartered" },
  { value: "7", label: "CI/CD integrations" },
  { value: "DORA", label: "Metrics day 1" },
];

function SectionTag({ children }) { return <div className="pill-badge font-body">{children}</div>; }

export function AboutPage() {
  return (
    <div data-testid="about-page" className="font-body">
      {/* Hero */}
      <section className="px-4 pt-12 pb-16 sm:pt-20">
        <div className="max-w-5xl mx-auto text-center">
          <SectionTag>About Pipelynx</SectionTag>
          <h1 className="font-display text-5xl sm:text-6xl font-bold tracking-tight leading-[1.05] mt-6 mb-6 text-slate-900" data-testid="about-heading">
            Built by engineers,<br />
            <span className="gradient-text">for engineering teams that ship daily.</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Pipelynx is a product of <strong className="text-slate-900 font-semibold">Sparkcurv Technologies Pvt. Ltd.</strong>,
            an independent software studio building tools for the post-DevOps generation.
            We believe the next decade of engineering velocity will be decided by what teams
            can <em className="not-italic underline decoration-indigo-400 decoration-2 underline-offset-4">see</em> —
            and we're building that vantage point, one pipeline at a time.
          </p>
        </div>

        <div className="mt-14 max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="about-stats">
          {STATS.map((s) => (
            <div key={s.label} className="glass-card rounded-2xl p-6 text-center lift-on-hover">
              <div className="font-display text-3xl font-bold gradient-text mb-1">{s.value}</div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Mission + Vision */}
      <section className="px-4 py-16" data-testid="mission-section">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="glass-card-strong rounded-3xl p-10 lift-on-hover">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-indigo-500/30">
              <Target size={22} className="text-white" strokeWidth={2} />
            </div>
            <SectionTag>Mission</SectionTag>
            <h2 className="font-display text-3xl font-bold tracking-tight mt-4 mb-4 text-slate-900 leading-tight">
              Give every team the situational awareness of a top-tier platform org.
            </h2>
            <p className="text-base text-slate-600 leading-relaxed">
              Most teams are flying blind. Their CI/CD systems generate gigabytes of signal a
              day — and almost none of it makes it back to the people who need it. We exist
              to close that loop.
            </p>
          </div>
          <div className="glass-card-strong rounded-3xl p-10 lift-on-hover">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500 to-violet-600 flex items-center justify-center mb-6 shadow-lg shadow-pink-500/30">
              <Compass size={22} className="text-white" strokeWidth={2} />
            </div>
            <SectionTag>Vision</SectionTag>
            <h2 className="font-display text-3xl font-bold tracking-tight mt-4 mb-4 text-slate-900 leading-tight">
              Become the default control plane for software delivery.
            </h2>
            <p className="text-base text-slate-600 leading-relaxed">
              From the first commit to the last 99.99%. Pipeline observability should be
              as standard as application monitoring. AI doesn't replace engineers — it
              gives them the leverage they've always deserved.
            </p>
          </div>
        </div>
      </section>

      {/* Story */}
      <section className="px-4 py-16" data-testid="story-section">
        <div className="max-w-4xl mx-auto glass-card rounded-3xl p-10 sm:p-14">
          <SectionTag>Our story</SectionTag>
          <h2 className="font-display text-4xl font-bold tracking-tight mt-4 mb-8 text-slate-900">
            From three open browser tabs<br />
            <span className="gradient-text">to one unified pane.</span>
          </h2>
          <div className="space-y-5 text-base text-slate-600 leading-relaxed">
            <p>
              Pipelynx started — as so many tools do — because the founders were tired of
              their own workflow. Between GitHub Actions, an internal Jenkins farm, and a
              freshly-migrated ArgoCD setup, simply answering <strong className="text-slate-900">"did the deploy ship?"</strong> required three tabs and a guess.
            </p>
            <p>
              The first prototype was a single FastAPI service that normalized webhooks from
              two platforms into a unified schema. It saved 30 minutes a day. Within a month,
              it had teams from three other companies asking for access.
            </p>
            <p>
              Today, Pipelynx ingests events from <strong className="text-slate-900">seven CI/CD platforms</strong>,
              calculates DORA metrics continuously, runs AI failure analysis on every
              broken pipeline, and routes alerts to the channels engineers actually read.
            </p>
            <p>
              We're a small team, headquartered in <strong className="text-slate-900">Nagercoil, Tamil Nadu</strong>,
              building in the open and shipping every week. Thank you for being early.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="px-4 py-16" data-testid="values-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <SectionTag>How we work</SectionTag>
            <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mt-4">
              Four principles.<br />
              <span className="gradient-text">No mission statement bingo.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {VALUES.map((v) => {
              const Icon = v.icon;
              return (
                <div key={v.title} className="glass-card rounded-3xl p-8 lift-on-hover" data-testid={`value-${v.title.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-5 shadow-lg shadow-indigo-500/30">
                    <Icon size={20} className="text-white" strokeWidth={2} />
                  </div>
                  <h3 className="font-display text-xl font-bold text-slate-900 mb-2">{v.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{v.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="px-4 py-16" data-testid="team-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <SectionTag>The team</SectionTag>
            <h2 className="font-display text-4xl font-bold tracking-tight mt-4">A small group with strong opinions.</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            {TEAM.map((m) => (
              <div key={m.name} className="glass-card rounded-3xl p-7 text-center lift-on-hover" data-testid={`team-${m.initials.toLowerCase().replace(/[^a-z0-9]/g, '')}`}>
                <div className="w-16 h-16 mx-auto mb-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-display font-bold text-lg shadow-lg shadow-indigo-500/30">
                  {m.initials}
                </div>
                <div className="font-display text-base font-bold text-slate-900 mb-1">{m.name}</div>
                <div className="text-xs text-slate-500 leading-relaxed">{m.role}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="px-4 py-16" data-testid="contact-section">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <SectionTag>Get in touch</SectionTag>
            <h2 className="font-display text-4xl font-bold tracking-tight mt-4">We'd love to hear from you.</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <a href="mailto:hello@pipelynx.io" className="glass-card-strong rounded-3xl p-8 lift-on-hover" data-testid="contact-email">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-5 shadow-lg shadow-blue-500/30">
                <Mail size={20} className="text-white" strokeWidth={2} />
              </div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-2">Email</div>
              <div className="font-display text-xl font-bold text-slate-900 mb-1">hello@pipelynx.io</div>
              <div className="text-sm text-slate-600">For partnerships, support, and feedback.</div>
              <div className="mt-4 text-sm font-semibold gradient-text inline-flex items-center gap-1">
                Send a message <ArrowRight size={14} />
              </div>
            </a>
            <div className="glass-card-strong rounded-3xl p-8" data-testid="contact-location">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center mb-5 shadow-lg shadow-pink-500/30">
                <MapPin size={20} className="text-white" strokeWidth={2} />
              </div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-2">Headquarters</div>
              <div className="font-display text-xl font-bold text-slate-900 mb-1">Sparkcurv Technologies Pvt. Ltd.</div>
              <div className="text-sm text-slate-600">Nagercoil, Tamil Nadu, India</div>
              <div className="mt-4 text-sm text-slate-400 font-medium">pipelynx.io</div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <Link to="/auth/register" className="btn-gradient inline-flex items-center gap-2 rounded-full px-8 py-4 text-sm font-semibold" data-testid="about-cta">
              Start using Pipelynx <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AboutPage;
