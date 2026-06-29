import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Calendar, Sparkles, Activity, TrendingUp, ShieldCheck } from "lucide-react";

const POSTS = [
  { slug: "dora-metrics-explained", title: "DORA metrics, explained without the buzzwords", excerpt: "Deployment Frequency, Lead Time, Change Failure Rate, MTTR. What they mean, why they matter, and how to measure them honestly.", date: "Coming soon", category: "Engineering", icon: TrendingUp, gradient: "from-blue-500 to-indigo-600" },
  { slug: "ai-failure-analysis", title: "How we use GPT-class models for CI/CD failure analysis", excerpt: "Behind-the-scenes look at our AI pipeline — prompt design, cost control, and why we cap context at 30 lines of logs.", date: "Coming soon", category: "Product", icon: Sparkles, gradient: "from-purple-500 to-pink-600" },
  { slug: "webhook-architecture", title: "Unified webhook ingestion across 7 CI/CD platforms", excerpt: "Why we ship a normalization layer instead of agents. The case for webhooks, and the schema we landed on.", date: "Coming soon", category: "Architecture", icon: Activity, gradient: "from-emerald-500 to-teal-600" },
  { slug: "multi-tenant-security", title: "Multi-tenant security in a pipeline observability tool", excerpt: "Organization-scoped isolation, JWT auth, and the trade-offs between simplicity and SOC 2 readiness.", date: "Coming soon", category: "Security", icon: ShieldCheck, gradient: "from-orange-500 to-red-600" },
];

function SectionTag({ children }) { return <div className="pill-badge font-body">{children}</div>; }

export function BlogPage() {
  return (
    <div data-testid="blog-page" className="font-body">
      <section className="px-4 pt-12 pb-12 sm:pt-20">
        <div className="max-w-5xl mx-auto text-center">
          <SectionTag>The Pipelynx Blog</SectionTag>
          <h1 className="font-display text-5xl sm:text-6xl font-bold tracking-tight leading-[1.05] mt-6 mb-6 text-slate-900" data-testid="blog-heading">
            Notes on shipping,<br />
            <span className="gradient-text">faster.</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Essays on CI/CD, DORA metrics, AI in developer tooling, and what we're
            building at Pipelynx. New posts roughly every other week.
          </p>
        </div>
      </section>

      <section className="px-4 py-12" data-testid="posts-section">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-10">
            <div>
              <SectionTag>Upcoming articles</SectionTag>
              <h2 className="font-display text-3xl font-bold tracking-tight mt-3">In the works</h2>
            </div>
            <div className="text-sm font-medium text-slate-500">4 drafts · 0 published</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5" data-testid="posts-grid">
            {POSTS.map((post) => {
              const Icon = post.icon;
              return (
                <article key={post.slug} className="glass-card rounded-3xl p-7 lift-on-hover flex flex-col" data-testid={`post-${post.slug}`}>
                  <div className="flex items-center justify-between mb-5">
                    <span className="pill-badge text-[10px] uppercase tracking-widest">{post.category}</span>
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${post.gradient} flex items-center justify-center shadow-lg`}>
                      <Icon size={18} className="text-white" strokeWidth={2} />
                    </div>
                  </div>
                  <h3 className="font-display text-xl font-bold text-slate-900 leading-snug mb-3">{post.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed flex-1 mb-6">{post.excerpt}</p>
                  <div className="pt-5 border-t border-slate-200 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                      <Calendar size={12} /> {post.date}
                    </div>
                    <span className="text-xs font-semibold gradient-text inline-flex items-center gap-1">
                      Notify me <ArrowRight size={11} />
                    </span>
                  </div>
                </article>
              );
            })}
          </div>

          {/* Subscribe strip */}
          <div className="mt-16 glass-card-strong rounded-3xl p-10 sm:p-12" data-testid="blog-subscribe">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div>
                <SectionTag>Stay in the loop</SectionTag>
                <h3 className="font-display text-3xl font-bold tracking-tight mt-4 mb-3 text-slate-900">
                  Get new posts in your inbox.
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  One email when we publish. No marketing fluff, no daily digest spam.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  placeholder="you@company.com"
                  data-testid="blog-subscribe-input"
                  className="flex-1 bg-white/80 backdrop-blur-md border border-slate-200 rounded-full px-5 py-3 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-900"
                />
                <a href="mailto:hello@pipelynx.io?subject=Subscribe%20to%20Pipelynx%20Blog" className="btn-gradient inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-semibold" data-testid="blog-subscribe-button">
                  Subscribe <ArrowRight size={14} />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 py-16" data-testid="blog-cta-section">
        <div className="max-w-3xl mx-auto glass-card rounded-3xl p-12 text-center">
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-4 text-slate-900">
            Reading is great. <span className="gradient-text">Shipping is better.</span>
          </h2>
          <p className="text-base text-slate-600 mb-8 max-w-xl mx-auto">
            Try Pipelynx free for 14 days. No credit card.
          </p>
          <Link to="/auth/register" className="btn-gradient inline-flex items-center gap-2 rounded-full px-8 py-4 text-sm font-semibold" data-testid="blog-cta">
            Start free <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}

export default BlogPage;
