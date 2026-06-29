import React, { useEffect, useState, useCallback } from "react";
import { metricsApi, runsApi } from "@/lib/api";
import { cn, formatDuration, formatRelativeTime, shortSha, SOURCE_LABELS } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { SourceIcon } from "@/components/SourceIcon";
import {
  Activity,
  Clock,
  AlertTriangle,
  Wrench,
  TrendingUp,
  TrendingDown,
  RefreshCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Legend,
} from "recharts";
import { Link } from "react-router-dom";

// Stable chart tick style constants (extracted to avoid inline object creation on every render)
const CHART_TICK_STYLE = { fontSize: 10, fontFamily: "IBM Plex Mono" };

// ============ Helper Components ============

function Section({ title, subtitle, children, className = "", action }) {
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

function Card({ children, className = "", testId, hoverable = false }) {
  return (
    <div
      className={cn(
        "bg-card border border-border p-5",
        hoverable && "hover:border-foreground/30 transition-colors",
        className
      )}
      data-testid={testId}
    >
      {children}
    </div>
  );
}

// Helper: determine trend color without nested ternaries
function getTrendColor(trend) {
  if (trend > 0) return "text-[#2ECC71]";
  if (trend < 0) return "text-[#FF3B30]";
  return "text-muted-foreground";
}

// Helper: determine trend icon without nested ternaries
function TrendIcon({ trend }) {
  if (trend > 0) return <TrendingUp size={10} />;
  if (trend < 0) return <TrendingDown size={10} />;
  return null;
}

function MetricCard({ icon: Icon, label, value, unit, trend, testId }) {
  return (
    <Card testId={testId}>
      <div className="flex items-start justify-between mb-4">
        <Icon size={16} strokeWidth={1.5} className="text-muted-foreground" />
        {trend != null && (
          <div
            className={cn(
              "flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider",
              getTrendColor(trend)
            )}
          >
            <TrendIcon trend={trend} />
            {trend !== 0 && `${trend > 0 ? "+" : ""}${trend}%`}
          </div>
        )}
      </div>
      <div className="text-label mb-2">{label}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-metric">{value}</span>
        {unit && <span className="text-xs font-mono text-muted-foreground uppercase">{unit}</span>}
      </div>
    </Card>
  );
}

function EmptyState({ title, description, action }) {
  return (
    <div className="border border-dashed border-border p-10 text-center">
      <div className="text-label mb-2">No data yet</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      {action}
    </div>
  );
}

// ============ Loading state ============
function LoadingBlock({ height = "h-32" }) {
  return (
    <div className={cn("border border-border bg-card", height, "flex items-center justify-center")}>
      <div className="text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
        Loading…
      </div>
    </div>
  );
}

// ============ Chart Tooltip ============
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      className="border border-border bg-black/80 backdrop-blur-xl px-3 py-2 text-xs font-mono"
      style={{ borderRadius: 0 }}
    >
      <div className="text-foreground mb-1.5 font-medium">{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span className="w-1.5 h-1.5" style={{ background: entry.color }} />
            {entry.dataKey}
          </span>
          <span className="text-foreground">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

// ============ Main Dashboard ============
export function DashboardPage() {
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState(null);
  const [dora, setDora] = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [topFailing, setTopFailing] = useState([]);
  const [recentRuns, setRecentRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    setRefreshing(true);
    try {
      const [s, d, ts, tf, runs] = await Promise.all([
        metricsApi.summary(days),
        metricsApi.dora(days),
        metricsApi.timeseries(days, "day"),
        metricsApi.topFailing(days, 5),
        runsApi.list({ limit: 5 }),
      ]);
      setSummary(s);
      setDora(d);
      setTimeseries(ts);
      setTopFailing(tf);
      setRecentRuns(runs.runs || []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [days]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(() => loadData(), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingBlock height="h-96" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="dashboard-page">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between mb-8 gap-4">
        <div>
          <div className="text-label mb-2">Pipeline Intelligence</div>
          <h1 className="text-3xl sm:text-4xl tracking-tight font-semibold">Overview</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="border border-border bg-card flex" data-testid="days-filter">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                data-testid={`days-filter-${d}`}
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
            onClick={loadData}
            disabled={refreshing}
            className="border border-border bg-card p-2 hover:border-foreground/30 transition-colors disabled:opacity-50"
            data-testid="refresh-button"
            title="Refresh"
          >
            <RefreshCw size={14} className={cn(refreshing && "animate-spin")} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      {/* DORA Metrics Row */}
      <Section title="DORA Metrics" subtitle="Engineering Performance">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="dora-metrics">
          <MetricCard
            icon={Activity}
            label="Deployment Frequency"
            value={dora?.deployment_frequency_per_day?.toFixed(2) || "0"}
            unit="per day"
            testId="metric-deployment-frequency"
          />
          <MetricCard
            icon={Clock}
            label="Lead Time"
            value={formatDuration(dora?.lead_time_seconds || 0)}
            unit=""
            testId="metric-lead-time"
          />
          <MetricCard
            icon={AlertTriangle}
            label="Change Failure Rate"
            value={dora?.change_failure_rate_percent?.toFixed(1) || "0"}
            unit="%"
            testId="metric-failure-rate"
          />
          <MetricCard
            icon={Wrench}
            label="MTTR"
            value={dora?.mttr_seconds ? formatDuration(dora.mttr_seconds) : "—"}
            unit=""
            testId="metric-mttr"
          />
        </div>
      </Section>

      {/* Summary stats */}
      <Section title="Activity" subtitle="Pipeline runs">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="summary-stats">
          <Card testId="stat-total-runs">
            <div className="text-label mb-2">Total runs</div>
            <div className="text-3xl font-light font-mono">{summary?.total_runs || 0}</div>
          </Card>
          <Card testId="stat-success-rate" className="border-l-2 border-l-[#2ECC71]/40">
            <div className="text-label mb-2">Success rate</div>
            <div className="text-3xl font-light font-mono">{summary?.success_rate || 0}%</div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">
              {summary?.successful_runs || 0} successful
            </div>
          </Card>
          <Card testId="stat-failures" className="border-l-2 border-l-[#FF3B30]/40">
            <div className="text-label mb-2">Failures</div>
            <div className="text-3xl font-light font-mono">{summary?.failed_runs || 0}</div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">
              {summary?.failure_rate || 0}% rate
            </div>
          </Card>
          <Card testId="stat-avg-duration">
            <div className="text-label mb-2">Avg duration</div>
            <div className="text-3xl font-light font-mono">
              {formatDuration(summary?.avg_duration_seconds || 0)}
            </div>
          </Card>
        </div>
      </Section>

      {/* Charts row */}
      <Section title="Runs over time" subtitle="Time series">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 p-6" testId="timeseries-chart">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold tracking-tight mb-1">Daily run volume</h3>
                <p className="text-xs text-muted-foreground">Last {days} days</p>
              </div>
            </div>
            {timeseries.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground font-mono text-xs uppercase tracking-wider">
                No runs in this period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={timeseries}>
                  <defs>
                    <linearGradient id="successGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2ECC71" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#2ECC71" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="failureGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#FF3B30" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#FF3B30" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="0" />
                  <XAxis
                    dataKey="bucket"
                    stroke="rgba(255,255,255,0.4)"
                    tick={CHART_TICK_STYLE}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.4)"
                    tick={CHART_TICK_STYLE}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="success"
                    stroke="#2ECC71"
                    strokeWidth={1.5}
                    fill="url(#successGrad)"
                  />
                  <Area
                    type="monotone"
                    dataKey="failure"
                    stroke="#FF3B30"
                    strokeWidth={1.5}
                    fill="url(#failureGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </Card>

          {/* Top failing pipelines */}
          <Card className="p-6" testId="top-failing">
            <h3 className="text-sm font-semibold tracking-tight mb-1">Top failing pipelines</h3>
            <p className="text-xs text-muted-foreground mb-4">Last {days} days</p>
            {topFailing.length === 0 ? (
              <div className="flex items-center justify-center h-48 text-muted-foreground font-mono text-xs uppercase tracking-wider">
                No failures
              </div>
            ) : (
              <div className="space-y-3" data-testid="top-failing-list">
                {topFailing.map((p, idx) => (
                  <div
                    key={`${p.pipeline_id || p.name}-${idx}`}
                    className="flex items-center justify-between gap-3 pb-3 border-b border-border last:border-0 last:pb-0"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <SourceIcon source={p.source} size={14} />
                      <div className="min-w-0">
                        <div className="text-sm truncate">{p.name}</div>
                        <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider truncate">
                          {p.repository || "—"}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[#FF3B30] font-mono text-sm">{p.failure_count}</div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
                        failures
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </Section>

      {/* Recent Runs */}
      <Section
        title="Recent runs"
        subtitle="Live feed"
        action={
          <Link
            to="/runs"
            className="text-xs uppercase tracking-wider font-medium text-muted-foreground hover:text-foreground transition-colors"
            data-testid="view-all-runs-link"
          >
            View all →
          </Link>
        }
      >
        {recentRuns.length === 0 ? (
          <EmptyState
            title="No pipeline runs yet"
            description="Connect a CI/CD integration to start receiving pipeline events."
            action={
              <Link
                to="/integrations"
                className="inline-block bg-foreground text-background px-4 py-2 text-xs uppercase tracking-wider font-medium hover:opacity-90 transition-opacity"
                data-testid="empty-add-integration-link"
              >
                Add integration →
              </Link>
            }
          />
        ) : (
          <Card className="p-0">
            <div className="divide-y divide-border" data-testid="recent-runs-list">
              {recentRuns.map((run) => (
                <Link
                  key={run.id}
                  to={`/runs/${run.id}`}
                  className="flex items-center gap-4 p-4 hover:bg-white/[0.02] transition-colors"
                  data-testid={`recent-run-${run.id}`}
                >
                  <SourceIcon source={run.source} size={16} />
                  <StatusBadge status={run.status} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">{run.name}</div>
                    <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">
                      {run.repository || SOURCE_LABELS[run.source]} · {run.branch || "—"}
                    </div>
                  </div>
                  <div className="hidden md:block text-xs font-mono text-muted-foreground">
                    {shortSha(run.commit_sha)}
                  </div>
                  <div className="hidden lg:block text-xs font-mono text-muted-foreground w-20 text-right">
                    {formatDuration(run.duration_seconds)}
                  </div>
                  <div className="text-xs font-mono text-muted-foreground w-20 text-right">
                    {formatRelativeTime(run.created_at)}
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
