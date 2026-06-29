import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Lock, X } from "lucide-react";

const PLAN_PRETTY = {
  free: "Free",
  basic: "Basic",
  business: "Business",
  enterprise: "Enterprise",
};

/**
 * Global 402 listener — listens for `pipelynx:upgrade-required` events emitted
 * by the axios interceptor and renders a single, in-place upgrade modal.
 */
export function UpgradeRequiredModal() {
  const [payload, setPayload] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onUpgrade = (event) => setPayload(event.detail || {});
    window.addEventListener("pipelynx:upgrade-required", onUpgrade);
    return () => window.removeEventListener("pipelynx:upgrade-required", onUpgrade);
  }, []);

  if (!payload) return null;

  const close = () => setPayload(null);
  const goToPricing = () => {
    const plan = payload.required_plan || "business";
    setPayload(null);
    navigate(`/pricing?highlight=${plan}`);
  };

  const currentPretty = PLAN_PRETTY[payload.current_plan] || "your current plan";
  const requiredPretty = PLAN_PRETTY[payload.required_plan] || "a higher plan";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
      data-testid="upgrade-required-modal"
      onClick={close}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="relative max-w-md w-full bg-card border border-border p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={close}
          className="absolute top-4 right-4 p-1.5 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Close"
          data-testid="upgrade-modal-close"
        >
          <X size={16} />
        </button>

        <div className="w-10 h-10 border border-border bg-white/[0.04] flex items-center justify-center mb-5">
          <Lock size={18} strokeWidth={1.5} />
        </div>

        <div className="text-label mb-2" data-testid="upgrade-modal-plan-row">
          {currentPretty} → {requiredPretty}
        </div>
        <h2 className="text-2xl tracking-tight font-semibold leading-tight mb-3" data-testid="upgrade-modal-heading">
          Upgrade required
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed mb-2" data-testid="upgrade-modal-detail">
          {payload.detail || "This feature is not included in your current plan."}
        </p>

        {typeof payload.limit === "number" && (
          <div className="mt-4 mb-2 border border-border p-3 bg-background/40 text-xs font-mono text-muted-foreground" data-testid="upgrade-modal-usage">
            Usage: <span className="text-foreground">{payload.current_usage ?? "—"}</span>
            <span> / </span>
            <span className="text-foreground">{payload.limit}</span>
          </div>
        )}

        <div className="flex items-center gap-3 mt-7">
          <button
            onClick={goToPricing}
            className="flex-1 bg-foreground text-background px-4 py-3 text-xs uppercase tracking-wider font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            data-testid="upgrade-modal-cta"
          >
            See plans
            <ArrowRight size={12} />
          </button>
          <button
            onClick={close}
            className="px-4 py-3 text-xs uppercase tracking-wider font-medium text-muted-foreground hover:text-foreground border border-border hover:border-foreground/40 transition-colors"
            data-testid="upgrade-modal-dismiss"
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  );
}

export default UpgradeRequiredModal;
