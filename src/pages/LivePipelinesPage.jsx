import React, { useEffect, useState, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { runsApi } from "@/lib/api";
import { cn, formatRelativeTime, formatDuration, SOURCE_LABELS, STATUS_DOT_COLORS } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { SourceIcon } from "@/components/SourceIcon";
import { Activity, Pause, Play, Radio, GitBranch, RefreshCw } from "lucide-react";

const REFRESH_INTERVAL_MS = 5000;
const FILTERS = ["all", "github", "jenkins", "gitlab"];

export function LivePipelinesPage() {
  const [data, setData] = useState({ in_flight: [], recent: [], sources: [], as_of: null });
  const [filter, setFilter] = useState("all");
  const [paused, setPaused] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pulse, setPulse] = useState(false);
  const timerRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const d = await runsApi.live();
      setData(d);
      setPulse(true);
      setTimeout(() => setPulse(false), 600);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (paused) {
      if (timerRef.current) clearInterval(timerRef.current);
      return undefined;
    }
    timerRef.current = setInterval(load, REFRESH_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [paused, load]);

  const inFlight = filter === "all"
    ? data.in_flight
    : data.in_flight.filter((r) => r.source === filter);
  const recent = filter === "all"
    ? data.recent
    : data.recent.filter((r) => r.source === filter);

  const totalInFlight = data.in_flight.length;
  const totalRunning = data.in_flight.filter((r) => r.status === "running").length;
  const totalQueued = data.in_flight.filter((r) => r.status === "queued").length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="live-pipelines-page">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-400 font-semibold mb-2">
            <span className={cn(
              "w-2 h-2 rounded-full",
              paused ? "bg-amber-400" : "bg-emerald-500 animate-pulse",
            )} />
            {paused ? "Paused" : "Live"}
            <span className="text-slate-300">·</span>
            <span className="font-mono normal-case tracking-normal">
              Updated {data.as_of ? formatRelativeTime(data.as_of) : "—"}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl tracking-tight font-bold text-slate-900 flex items-center gap-3">
            <span className="relative">
              <Radio size={28} className="text-indigo-600" strokeWidth={2} />
              {pulse && (
                <span className="absolute inset-0 rounded-full bg-indigo-400/40 animate-ping" />
              )}
            </span>
            Live Pipelines
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-xl">
            Real-time view of every in-flight run across GitHub, Jenkins, GitLab and more — auto-refreshing every 5 seconds.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPaused((p) => !p)}
            className={cn(
              "px-3 py-2 rounded-full text-xs font-semibold flex items-center gap-2 transition-colors border",
              paused
                ? "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
                : "bg-white/70 text-slate-700 border-slate-200 hover:bg-white",
            )}
            data-testid="live-pause-button"
          >
            {paused ? <Play size={12} strokeWidth={2.5} /> : <Pause size={12} strokeWidth={2.5} />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            onClick={load}
            className="px-3 py-2 rounded-full text-xs font-semibold flex items-center gap-2 bg-white/70 text-slate-700 border border-slate-200 hover:bg-white transition-colors"
            data-testid="live-refresh-button"
          >
            <RefreshCw size={12} strokeWidth={2.5} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatTile label="In-flight" value={totalInFlight} color="indigo" pulse />
        <StatTile label="Running" value={totalRunning} color="blue" />
        <StatTile label="Queued" value={totalQueued} color="amber" />
        <StatTile label="Sources active" value={data.sources.length} color="slate" />
      </div>

      {/* Per-source breakdown */}
      <div className="glass-card rounded-2xl p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">By platform</div>
          <div className="flex items-center gap-1.5">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-2.5 py-1 rounded-full text-[10px] uppercase tracking-wider font-semibold transition-colors",
                  filter === f
                    ? "bg-indigo-600 text-white"
                    : "bg-white/70 text-slate-600 border border-slate-200 hover:bg-white",
                )}
                data-testid={`live-filter-${f}`}
              >
                {f === "all" ? "All sources" : SOURCE_LABELS[f] || f}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          {data.sources.length === 0 && (
            <div className="col-span-full text-xs text-slate-400 font-mono py-6 text-center">
              No pipeline runs yet — connect an integration to see live activity here.
            </div>
          )}
          {data.sources.map((s) => (
            <div key={s.source} className="rounded-xl bg-white/70 border border-slate-200 p-3" data-testid={`source-card-${s.source}`}>
              <div className="flex items-center gap-2 mb-2">
                <SourceIcon source={s.source} size={14} />
                <div className="text-xs font-semibold text-slate-800 truncate">{SOURCE_LABELS[s.source] || s.source}</div>
              </div>
              <div className="grid grid-cols-3 gap-1 text-[10px] font-mono">
                <Stat dot="bg-blue-500" v={s.running} l="run" />
                <Stat dot="bg-amber-500" v={s.queued} l="q" />
                <Stat dot="bg-rose-500" v={s.failure} l="fail" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* In-flight runs list */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          In-flight ({inFlight.length})
        </h2>
        {loading && inFlight.length === 0 ? (
          <div className="glass-card rounded-2xl h-32 flex items-center justify-center text-xs text-slate-400 font-mono uppercase tracking-wider">
            Connecting…
          </div>
        ) : null}
        {!loading && inFlight.length === 0 ? (
          <div className="glass-card rounded-2xl p-10 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 mb-3">
              <Activity size={20} strokeWidth={2} />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-1">No active builds right now</h3>
            <p className="text-sm text-slate-500">
              When your CI/CD pipelines start running, they&apos;ll appear here instantly.
            </p>
          </div>
        ) : null}
        <div className="space-y-2" data-testid="live-in-flight-list">
          {inFlight.map((run) => (
            <LiveRunCard key={run.id} run={run} />
          ))}
        </div>
      </section>

      {/* Recent (completed) */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Most recent
        </h2>
        <div className="glass-card rounded-2xl divide-y divide-slate-100 overflow-hidden">
          {recent.length === 0 && (
            <div className="p-6 text-xs text-slate-400 font-mono text-center">No runs yet</div>
          )}
          {recent.map((run) => (
            <Link
              key={run.id}
              to={`/runs/${run.id}`}
              className="flex items-center gap-3 p-3 hover:bg-white/60 transition-colors"
              data-testid={`recent-run-${run.id}`}
            >
              <span className={cn("w-1.5 h-8 rounded-full", STATUS_DOT_COLORS[run.status] || "bg-slate-300")} />
              <StatusBadge status={run.status} />
              <SourceIcon source={run.source} size={14} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-800 truncate">{run.name}</div>
                <div className="text-[11px] text-slate-500 font-mono truncate">
                  {run.repository || "—"} · {run.branch || "—"}
                </div>
              </div>
              <div className="text-[11px] font-mono text-slate-500 whitespace-nowrap">
                {formatDuration(run.duration_seconds)} · {formatRelativeTime(run.created_at)}
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatTile({ label, value, color, pulse }) {
  const palette = {
    indigo: "from-indigo-500 to-purple-600",
    blue: "from-blue-500 to-cyan-500",
    amber: "from-amber-400 to-orange-500",
    slate: "from-slate-500 to-slate-700",
  }[color] || "from-slate-500 to-slate-700";
  return (
    <div className="glass-card rounded-2xl p-4 relative overflow-hidden" data-testid={`stat-${label.toLowerCase().replace(/ /g, "-")}`}>
      <div className={cn("absolute inset-0 opacity-[0.07] bg-gradient-to-br", palette)} />
      <div className="relative">
        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold flex items-center gap-1.5">
          {pulse && value > 0 && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
          {label}
        </div>
        <div className={cn("font-display text-3xl font-bold mt-1 bg-clip-text text-transparent bg-gradient-to-br", palette)}>
          {value}
        </div>
      </div>
    </div>
  );
}

function Stat({ dot, v, l }) {
  return (
    <div className="flex items-center gap-1 text-slate-600">
      <span className={cn("w-1.5 h-1.5 rounded-full", dot)} />
      <span className="font-semibold">{v}</span>
      <span className="text-slate-400">{l}</span>
    </div>
  );
}

function LiveRunCard({ run }) {
  const isRunning = run.status === "running";
  const elapsed = run.started_at
    ? Math.max(0, Math.floor((Date.now() - new Date(run.started_at).getTime()) / 1000))
    : run.duration_seconds || 0;
  return (
    <Link
      to={`/runs/${run.id}`}
      className={cn(
        "block glass-card rounded-2xl p-4 transition-all hover:shadow-md relative overflow-hidden",
        isRunning && "border-blue-200",
      )}
      data-testid={`live-run-${run.id}`}
    >
      {isRunning && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-500 animate-shimmer bg-[length:200%_100%]" />
      )}
      <div className="flex items-start gap-3">
        <div className={cn(
          "w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0",
          isRunning ? "bg-blue-50" : "bg-amber-50",
        )}>
          <SourceIcon source={run.source} size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <StatusBadge status={run.status} />
            <span className="text-sm font-semibold text-slate-800 truncate">{run.name}</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
            <span className="inline-flex items-center gap-1">
              <GitBranch size={10} strokeWidth={2} />
              {run.branch || "—"}
            </span>
            <span>{run.repository || "—"}</span>
            <span className="text-slate-400">·</span>
            <span>{run.author || "—"}</span>
          </div>
          {run.commit_message && (
            <div className="text-xs text-slate-500 mt-1 truncate italic">{run.commit_message}</div>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-xs font-mono font-semibold text-slate-700">
            {formatDuration(elapsed)}
          </div>
          <div className="text-[10px] text-slate-400 uppercase tracking-wider">
            {isRunning ? "elapsed" : "duration"}
          </div>
        </div>
      </div>
    </Link>
  );
}
