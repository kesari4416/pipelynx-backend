import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { billingApi } from "@/lib/api";
import { toast } from "sonner";
import { Check, X, ArrowRight, Sparkles, Zap, Building2, Rocket, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ============ Plan catalog ============
// Public visitors see the marketing version; values must match billing_service.PLANS
const PLANS = [
  {
    id: "free", name: "Free", tagline: "For solo developers getting started",
    price: { monthly: 0, yearly: 0 }, pricePer: "Forever free",
    icon: Sparkles, gradient: "from-slate-500 to-slate-700",
    features: [
      { text: "1 organization · 1 user", included: true },
      { text: "Up to 1,000 pipeline runs / month", included: true },
      { text: "3 CI/CD integrations", included: true },
      { text: "7-day run history", included: true },
      { text: "Basic DORA metrics", included: true },
      { text: "AI failure analysis", included: false },
      { text: "Slack / webhook alerts", included: false },
    ],
    cta: "Get started",
    ctaLink: "/auth/register",
  },
  {
    id: "basic", name: "Basic", tagline: "For small teams shipping daily",
    price: { monthly: 29, yearly: 24 }, pricePer: "per user / month",
    icon: Zap, gradient: "from-blue-500 to-indigo-600",
    features: [
      { text: "Up to 5 users", included: true },
      { text: "Up to 10,000 pipeline runs / month", included: true },
      { text: "10 CI/CD integrations", included: true },
      { text: "30-day run history", included: true },
      { text: "Full DORA dashboard", included: true },
      { text: "AI: 10 analyses / day", included: true },
      { text: "Email + Slack alerts", included: true },
    ],
    cta: "Choose Basic",
    ctaLink: "/auth/register",
  },
  {
    id: "business", name: "Business", tagline: "For engineering orgs scaling",
    price: { monthly: 79, yearly: 65 }, pricePer: "per user / month",
    icon: Building2, gradient: "from-indigo-500 via-purple-500 to-pink-500",
    highlight: true, badge: "Most Popular",
    features: [
      { text: "Up to 25 users", included: true },
      { text: "Up to 100,000 pipeline runs / month", included: true },
      { text: "Unlimited integrations", included: true },
      { text: "90-day run history", included: true },
      { text: "AI: unlimited analyses", included: true },
      { text: "Anomaly + pattern detection", included: true },
      { text: "Slack + Webhook + PagerDuty", included: true },
    ],
    cta: "Choose Business",
    ctaLink: "/auth/register",
  },
  {
    id: "enterprise", name: "Enterprise", tagline: "For platform teams at scale",
    customPrice: "Custom", icon: Rocket, gradient: "from-amber-500 to-orange-600",
    features: [
      { text: "Unlimited everything", included: true },
      { text: "SSO / SAML + SCIM", included: true },
      { text: "RBAC + audit logs", included: true },
      { text: "Self-hosted / VPC option", included: true },
      { text: "Custom integrations", included: true },
      { text: "Dedicated AI tuning", included: true },
      { text: "24/7 support · custom SLA", included: true },
    ],
    cta: "Contact Sales", isExternal: true,
    ctaLink: "mailto:sales@pipelynx.io?subject=Pipelynx%20Enterprise%20Inquiry",
  },
];

// ============ Price display ============
function PriceDisplay({ plan, billing }) {
  if (plan.customPrice) {
    return (
      <div className="mb-6">
        <div className="font-display text-4xl font-bold text-slate-900">{plan.customPrice}</div>
        <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Talk to us</div>
      </div>
    );
  }
  const price = billing === "yearly" ? plan.price.yearly : plan.price.monthly;
  return (
    <div className="mb-6">
      <div className="flex items-baseline gap-1">
        <span className="text-xl font-semibold text-slate-500">$</span>
        <span className="font-display text-5xl font-bold text-slate-900 tracking-tight">{price}</span>
      </div>
      {price === 0 ? (
        <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Forever free</div>
      ) : (
        <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">
          {plan.pricePer} {billing === "yearly" && "· billed annually"}
        </div>
      )}
    </div>
  );
}

function FeatureItem({ feature }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      {feature.included ? (
        <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Check size={12} className="text-emerald-600" strokeWidth={3} />
        </div>
      ) : (
        <div className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <X size={12} className="text-slate-400" strokeWidth={2.5} />
        </div>
      )}
      <span className={cn("leading-relaxed", feature.included ? "text-slate-700" : "text-slate-400 line-through")}>
        {feature.text}
      </span>
    </li>
  );
}

function PlanCard({ plan, billing, onSelect, busyPlanId, highlightPlanId }) {
  const Icon = plan.icon;
  const isBusy = busyPlanId === plan.id;
  const isExternal = Boolean(plan.isExternal);
  const isHighlighted = highlightPlanId === plan.id;

  const Wrapper = ({ children }) => (
    <div
      className={cn(
        "relative rounded-3xl p-7 flex flex-col h-full transition-all duration-300",
        plan.highlight ? "glass-card-strong lift-on-hover" : "glass-card lift-on-hover",
        plan.highlight && "ring-1 ring-indigo-200/60",
        isHighlighted && "ring-2 ring-emerald-400 shadow-2xl shadow-emerald-500/20"
      )}
      data-testid={`plan-${plan.id}`}
    >
      {plan.badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-[10px] uppercase tracking-widest font-bold shadow-lg shadow-indigo-500/30" data-testid="plan-badge">
          {plan.badge}
        </div>
      )}
      {isHighlighted && (
        <div className="absolute -top-3 right-6 px-3 py-1 rounded-full bg-emerald-500 text-white text-[10px] uppercase tracking-widest font-bold shadow-lg" data-testid="plan-recommended-badge">
          Recommended
        </div>
      )}
      {children}
    </div>
  );

  return (
    <Wrapper>
      <div className="mb-5">
        <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center mb-4 shadow-lg`}>
          <Icon size={20} className="text-white" strokeWidth={2} />
        </div>
        <h3 className="font-display text-2xl font-bold text-slate-900 mb-1">{plan.name}</h3>
        <p className="text-xs text-slate-500 leading-relaxed">{plan.tagline}</p>
      </div>

      <PriceDisplay plan={plan} billing={billing} />

      {/* CTA */}
      {isExternal ? (
        <a
          href={plan.ctaLink}
          className={cn(
            "block text-center rounded-full px-5 py-3 text-xs uppercase tracking-wider font-bold mb-6 transition-all",
            "btn-glass"
          )}
          data-testid={`plan-cta-${plan.id}`}
        >
          <span className="inline-flex items-center justify-center gap-2">{plan.cta} <ArrowRight size={12} /></span>
        </a>
      ) : (
        <button
          type="button"
          onClick={() => onSelect(plan)}
          disabled={isBusy}
          className={cn(
            "rounded-full px-5 py-3 text-xs uppercase tracking-wider font-bold mb-6 transition-all inline-flex items-center justify-center gap-2 w-full disabled:opacity-60 disabled:cursor-not-allowed",
            plan.highlight ? "btn-gradient" : "btn-glass"
          )}
          data-testid={`plan-cta-${plan.id}`}
        >
          {isBusy ? <Loader2 size={12} className="animate-spin" /> : null}
          {isBusy ? "Saving…" : plan.cta}
          {!isBusy && <ArrowRight size={12} />}
        </button>
      )}

      {/* Features */}
      <ul className="space-y-3 flex-1 border-t border-slate-200 pt-5">
        {plan.features.map((f) => (
          <FeatureItem key={f.text} feature={f} />
        ))}
      </ul>
    </Wrapper>
  );
}

// ============ Main page ============
export function PricingPage() {
  const [billing, setBilling] = useState("monthly");
  const [region, setRegion] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [busyPlanId, setBusyPlanId] = useState(null);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const highlightPlanId = searchParams.get("highlight");
  const isAuthenticated = Boolean(user);

  useEffect(() => {
    billingApi.region().then(setRegion).catch(() => setRegion(null));
    if (isAuthenticated) {
      billingApi.subscription().then(setSubscription).catch(() => setSubscription(null));
    }
  }, [isAuthenticated]);

  const handleSelectPlan = useCallback(
    async (plan) => {
      if (!isAuthenticated) {
        navigate(`/auth/register?plan=${plan.id}&cycle=${billing}`);
        return;
      }
      setBusyPlanId(plan.id);
      try {
        const result = await billingApi.recordIntent({
          plan: plan.id,
          billing_cycle: billing,
          seats: 1,
        });
        setSubscription(result.subscription);
        toast.success(
          plan.id === "free" ? "Free plan activated." : `${plan.name} plan selected.`,
          { description: result.next_step }
        );
      } catch (err) {
        const detail = err?.response?.data?.detail || "Could not record your selection.";
        toast.error("Plan selection failed", { description: detail });
      } finally {
        setBusyPlanId(null);
      }
    },
    [billing, isAuthenticated, navigate]
  );

  const currencyLabel = region?.currency === "INR" ? "INR" : "USD";
  const providerLabel = region?.provider === "razorpay" ? "Razorpay" : "Stripe";

  return (
    <div className="bg-transparent font-body" data-testid="pricing-page">
      <section className="px-4 pt-12 pb-12 sm:pt-20">
        <div className="max-w-5xl mx-auto text-center">
          <div className="pill-badge font-body mx-auto">Pricing</div>
          <h1 className="font-display text-5xl sm:text-6xl font-bold tracking-tight leading-[1.05] mt-6 mb-6 text-slate-900">
            Pipeline intelligence,<br />
            <span className="gradient-text">priced for every team.</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Start free. Upgrade as you scale. No credit card required for the free plan.
          </p>

          {/* Region + current plan strip */}
          <div className="flex items-center justify-center gap-3 mt-7 flex-wrap" data-testid="pricing-region-strip">
            {region && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-md border border-slate-200 text-xs font-medium text-slate-700" data-testid="region-badge">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-status-pulse" />
                {region.region} · {currencyLabel} · {providerLabel}
              </span>
            )}
            {isAuthenticated && subscription && (
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border",
                  subscription.status === "active" && "bg-emerald-50 text-emerald-700 border-emerald-200",
                  subscription.status === "intent" && "bg-amber-50 text-amber-700 border-amber-200",
                  subscription.status === "contact_sales" && "bg-blue-50 text-blue-700 border-blue-200",
                  subscription.status === "cancelled" && "bg-rose-50 text-rose-700 border-rose-200",
                )}
                data-testid="current-plan-badge"
              >
                Current: {subscription.plan} · {subscription.status}
              </span>
            )}
          </div>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-1 mt-8 p-1 rounded-full glass-card" data-testid="billing-toggle">
            <button
              onClick={() => setBilling("monthly")}
              className={cn(
                "px-5 py-2 rounded-full text-sm font-semibold transition-all",
                billing === "monthly" ? "bg-white text-slate-900 shadow-md" : "text-slate-600 hover:text-slate-900"
              )}
              data-testid="billing-monthly"
            >
              Monthly
            </button>
            <button
              onClick={() => setBilling("yearly")}
              className={cn(
                "px-5 py-2 rounded-full text-sm font-semibold transition-all inline-flex items-center gap-2",
                billing === "yearly" ? "bg-white text-slate-900 shadow-md" : "text-slate-600 hover:text-slate-900"
              )}
              data-testid="billing-yearly"
            >
              Yearly
              <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-[10px] font-bold">
                SAVE 17%
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Plans grid */}
      <section className="px-4 pb-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {PLANS.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                billing={billing}
                onSelect={handleSelectPlan}
                busyPlanId={busyPlanId}
                highlightPlanId={highlightPlanId}
              />
            ))}
          </div>

          {/* Trust strip */}
          <div className="mt-16 glass-card rounded-3xl p-8 sm:p-10 grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-2">Cancel anytime</div>
              <p className="text-sm text-slate-600 leading-relaxed">Month-to-month billing. No long-term contracts.</p>
            </div>
            <div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-2">All plans include</div>
              <p className="text-sm text-slate-600 leading-relaxed">Unified webhook gateway, real-time runs, encryption at rest, multi-tenancy.</p>
            </div>
            <div>
              <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-2">Need something custom?</div>
              <p className="text-sm text-slate-600 leading-relaxed">
                <a href="mailto:sales@pipelynx.io?subject=Pipelynx%20Custom%20Plan" className="font-semibold gradient-text hover:opacity-80">Talk to sales →</a>
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default PricingPage;
