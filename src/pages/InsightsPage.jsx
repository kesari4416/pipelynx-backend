import React, { useEffect, useState, useCallback } from "react";
import { aiApi } from "@/lib/api";
import { cn, formatDuration, formatRelativeTime, SOURCE_LABELS } from "@/lib/utils";
import { SourceIcon } from "@/components/SourceIcon";
import { Link } from "react-router-dom";
import {
  Sparkles,
  Loader2,
  AlertTriangle,
  TrendingUp,
  Zap,
  RefreshCw,
  Activity,
} from "lucide-react";

function Section({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={cn("mb-10", className)}>
      <div className="flex items-end justify-between mb-4">
        <div>
          {subtitle && <div className="text-label mb-1">{subtitle}</div>}
          <h2 className="text-xl tracking-tight font-semibold">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function Card({ children, className = "", testId }) {
  return (
    <div className={cn("bg-card border border-border p-5", className)} data-testid={testId}>
      {children}
    </div>
  );
}

function LoadingBlock({ label = "Loading…" }) {
  return (
    <div className="border border-border bg-card h-32 flex items-center justify-center text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
      {label}
    </div>
  );
}

export function InsightsPage() {
  const [days, setDays] = useState(7);
  const [digest, setDigest] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loadingDigest, setLoadingDigest] = useState(false);
  const [loadingPatterns, setLoadingPatterns] = useState(false);
  const [loadingAnomalies, setLoadingAnomalies] = useState(false);

  const loadDigest = useCallback(async () => {
    setLoadingDigest(true);
    try {
      const result = await aiApi.digest();
      setDigest(result);
    } catch (err) {
      setDigest({ digest: `Error: ${err.message}`, generated_at: null });
    } finally {
      setLoadingDigest(false);
    }
  }, []);

  const loadPatterns = useCallback(async () => {
    setLoadingPatterns(true);
    try {
      const result = await aiApi.patterns(days);
      setPatterns(result);
    } finally {
      setLoadingPatterns(false);
    }
  }, [days]);

  const loadAnomalies = useCallback(async () => {
    setLoadingAnomalies(true);
    try {
      const result = await aiApi.anomalies(30);
      setAnomalies(result);
    } finally {
      setLoadingAnomalies(false);
    }
  }, []);

  useEffect(() => {
    loadAnomalies();
  }, [loadAnomalies]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="insights-page">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <div className="text-label mb-2 flex items-center gap-2">
            <Sparkles size={12} strokeWidth={1.5} className="text-[#F59E0B]" />
            AI Intelligence
          </div>
          <h1 className="text-3xl sm:text-4xl tracking-tight font-semibold">Insights</h1>
        </div>
      </div>

      {/* Weekly Digest */}
      <Section
        title="Weekly Digest"
        subtitle="Executive summary"
        action={
          <button
            onClick={loadDigest}
            disabled={loadingDigest}
            className="border border-border hover:border-foreground/30 px-3 py-1.5 text-xs uppercase tracking-wider font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
            data-testid="generate-digest-button"
          >
            {loadingDigest ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Sparkles size={12} strokeWidth={1.5} />
            )}
            {digest ? "Regenerate" : "Generate digest"}
          </button>
        }
      >
        {!digest && !loadingDigest && (
          <Card>
            <div className="border border-dashed border-border p-8 text-center">
              <Sparkles size={20} className="mx-auto text-[#F59E0B] mb-3" strokeWidth={1.5} />
              <p className="text-sm text-muted-foreground mb-1">No digest yet</p>
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Click "Generate digest" for AI-powered weekly insights
              </p>
            </div>
          </Card>
        )}
        {loadingDigest && <LoadingBlock label="Generating digest with GPT-4o…" />}
        {digest && !loadingDigest && (
          <Card testId="digest-card">
            <div className="border-l-2 border-[#F59E0B]/40 pl-4">
              <div className="text-label mb-3 flex items-center justify-between">
                <span>Generated {formatRelativeTime(digest.generated_at)}</span>
                {digest.stats && (
                  <div className="flex gap-4 font-mono text-[10px]">
                    <span>{digest.stats.total_runs} runs</span>
                    <span>{digest.stats.success_rate}% success</span>
                    <span>{digest.stats.deployment_frequency}/day</span>
                  </div>
                )}
              </div>
              <p className="text-sm leading-relaxed whitespace-pre-line">{digest.digest}</p>
            </div>
          </Card>
        )}
      </Section>

      {/* Failure Patterns */}
      <Section
        title="Failure Patterns"
        subtitle="Cross-pipeline correlation"
        action={
          <div className="flex items-center gap-2">
            <div className="border border-border bg-card flex">
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  data-testid={`patterns-days-${d}`}
                  className={cn(
                    "px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors",
                    days === d
                      ? "bg-foreground text-background"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {d}D
                </button>
              ))}
            </div>
            <button
              onClick={loadPatterns}
              disabled={loadingPatterns}
              className="border border-border hover:border-foreground/30 px-3 py-1.5 text-xs uppercase tracking-wider font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
              data-testid="analyze-patterns-button"
            >
              {loadingPatterns ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} strokeWidth={1.5} />}
              {patterns ? "Re-analyze" : "Analyze patterns"}
            </button>
          </div>
        }
      >
        {!patterns && !loadingPatterns && (
          <Card>
            <div className="border border-dashed border-border p-8 text-center">
              <AlertTriangle size={20} className="mx-auto text-muted-foreground mb-3" strokeWidth={1.5} />
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Click "Analyze patterns" to detect cross-pipeline failure correlations
              </p>
            </div>
          </Card>
        )}
        {loadingPatterns && <LoadingBlock label="Analyzing failure patterns…" />}
        {patterns && !loadingPatterns && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="patterns-grid">
            <Card>
              <div className="text-label mb-3 flex items-center gap-2">
                <TrendingUp size={12} strokeWidth={1.5} />
                Patterns detected
              </div>
              {(patterns.patterns || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No patterns detected</p>
              ) : (
                <ul className="space-y-2">
                  {patterns.patterns.map((p, idx) => (
                    <li key={idx} className="text-sm flex gap-2">
                      <span className="text-muted-foreground font-mono">·</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card className="border-l-2 border-l-destructive/40">
              <div className="text-label mb-3 flex items-center gap-2">
                <AlertTriangle size={12} strokeWidth={1.5} className="text-destructive" />
                Systemic issues
              </div>
              {(patterns.systemic_issues || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">None identified</p>
              ) : (
                <ul className="space-y-2">
                  {patterns.systemic_issues.map((p, idx) => (
                    <li key={idx} className="text-sm flex gap-2">
                      <span className="text-destructive font-mono">!</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card className="border-l-2 border-l-[#F59E0B]/40">
              <div className="text-label mb-3 flex items-center gap-2">
                <Zap size={12} strokeWidth={1.5} className="text-[#F59E0B]" />
                Priority actions
              </div>
              {(patterns.priority_actions || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No actions required</p>
              ) : (
                <ul className="space-y-2">
                  {patterns.priority_actions.map((p, idx) => (
                    <li key={idx} className="text-sm flex gap-2">
                      <span className="text-[#F59E0B] font-mono">→</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        )}
      </Section>

      {/* Anomalies */}
      <Section
        title="Duration Anomalies"
        subtitle="Statistical outliers"
        action={
          <button
            onClick={loadAnomalies}
            disabled={loadingAnomalies}
            className="border border-border bg-card p-2 hover:border-foreground/30 transition-colors disabled:opacity-50"
            data-testid="refresh-anomalies-button"
            title="Refresh"
          >
            <RefreshCw size={14} className={cn(loadingAnomalies && "animate-spin")} strokeWidth={1.5} />
          </button>
        }
      >
        {loadingAnomalies ? (
          <LoadingBlock label="Detecting anomalies…" />
        ) : anomalies.length === 0 ? (
          <Card>
            <div className="border border-dashed border-border p-8 text-center">
              <Activity size={20} className="mx-auto text-[#2ECC71] mb-3" strokeWidth={1.5} />
              <p className="text-sm font-medium mb-1">No anomalies detected</p>
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                All pipeline durations are within expected ranges
              </p>
            </div>
          </Card>
        ) : (
          <Card className="p-0" testId="anomalies-list">
            <div className="divide-y divide-border">
              {anomalies.map((a) => (
                <Link
                  key={a.run_id}
                  to={`/runs/${a.run_id}`}
                  className="flex items-center gap-4 p-4 hover:bg-white/[0.02] transition-colors"
                  data-testid={`anomaly-${a.run_id}`}
                >
                  <SourceIcon source={a.source} size={16} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">{a.name}</div>
                    <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider truncate">
                      {a.repository || SOURCE_LABELS[a.source]}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-mono text-[#F59E0B]">
                      {a.deviation_factor}× slower
                    </div>
                    <div className="text-[10px] text-muted-foreground font-mono">
                      {formatDuration(a.duration_seconds)} vs {formatDuration(a.expected_duration_seconds)}
                    </div>
                  </div>
                  <div className="text-xs font-mono text-muted-foreground w-20 text-right">
                    {formatRelativeTime(a.created_at)}
                  </div>
                </Link>
              ))}
            </div>
          </Card>
        )}
      </Section>
    </div>
  );
}
