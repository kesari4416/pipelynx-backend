import React, { useEffect, useState, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { runsApi, aiApi } from "@/lib/api";
import {
  cn,
  formatDuration,
  formatRelativeTime,
  formatDateTime,
  shortSha,
  SOURCE_LABELS,
  SOURCE_KEYS,
} from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { SourceIcon } from "@/components/SourceIcon";
import { ArrowLeft, ExternalLink, GitBranch, GitCommit, User, Clock, ChevronLeft, ChevronRight, X, Sparkles, Loader2 } from "lucide-react";

const STATUS_FILTERS = ["success", "failure", "running", "queued", "cancelled", "skipped"];

// ============ Runs List Page ============
export function RunsListPage() {
  const [runs, setRuns] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sourceFilter, setSourceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 25;

  const loadRuns = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit, skip: page * limit };
      if (sourceFilter) params.source = sourceFilter;
      if (statusFilter) params.status = statusFilter;
      const data = await runsApi.list(params);
      setRuns(data.runs || []);
      setTotal(data.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, sourceFilter, statusFilter]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  // Reset to first page when filters change
  useEffect(() => {
    setPage(0);
  }, [sourceFilter, statusFilter]);

  const clearFilters = () => {
    setSourceFilter("");
    setStatusFilter("");
  };

  const hasFilters = sourceFilter || statusFilter;
  const totalPages = Math.ceil(total / limit);

  // Render content based on state - avoids nested ternaries
  const renderContent = () => {
    if (loading) {
      return (
        <div className="border border-border bg-card h-64 flex items-center justify-center text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
          Loading runs…
        </div>
      );
    }
    if (runs.length === 0) {
      return (
        <div className="border border-dashed border-border p-16 text-center">
          <div className="text-label mb-2">Empty</div>
          <h3 className="text-lg font-semibold mb-2">No runs found</h3>
          <p className="text-sm text-muted-foreground">
            {hasFilters
              ? "Try adjusting your filters."
              : "Connect an integration and trigger a pipeline to see runs here."}
          </p>
        </div>
      );
    }
    return (
      <>
        <div className="border border-border bg-card overflow-x-auto" data-testid="runs-table">
          <table className="w-full">
            <thead className="border-b border-border">
              <tr className="text-label">
                <th className="text-left p-3 font-medium">Source</th>
                <th className="text-left p-3 font-medium">Status</th>
                <th className="text-left p-3 font-medium">Pipeline</th>
                <th className="text-left p-3 font-medium hidden md:table-cell">Repository</th>
                <th className="text-left p-3 font-medium hidden lg:table-cell">Branch</th>
                <th className="text-left p-3 font-medium hidden lg:table-cell">Commit</th>
                <th className="text-right p-3 font-medium hidden md:table-cell">Duration</th>
                <th className="text-right p-3 font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-border last:border-0 hover:bg-white/[0.02] transition-colors cursor-pointer group"
                  onClick={() => (window.location.href = `/runs/${run.id}`)}
                  data-testid={`run-row-${run.id}`}
                >
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <SourceIcon source={run.source} size={14} />
                      <span className="text-xs text-muted-foreground uppercase tracking-wider hidden sm:inline">
                        {run.source}
                      </span>
                    </div>
                  </td>
                  <td className="p-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="p-3">
                    <Link
                      to={`/runs/${run.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm hover:text-foreground/80"
                    >
                      {run.name}
                    </Link>
                  </td>
                  <td className="p-3 hidden md:table-cell text-xs font-mono text-muted-foreground">
                    {run.repository || "—"}
                  </td>
                  <td className="p-3 hidden lg:table-cell text-xs font-mono text-muted-foreground">
                    {run.branch ? (
                      <span className="inline-flex items-center gap-1">
                        <GitBranch size={10} strokeWidth={1.5} />
                        {run.branch}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="p-3 hidden lg:table-cell text-xs font-mono text-muted-foreground">
                    {shortSha(run.commit_sha)}
                  </td>
                  <td className="p-3 hidden md:table-cell text-right text-xs font-mono text-muted-foreground">
                    {formatDuration(run.duration_seconds)}
                  </td>
                  <td className="p-3 text-right text-xs font-mono text-muted-foreground">
                    {formatRelativeTime(run.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-xs font-mono text-muted-foreground">
              Page {page + 1} of {totalPages}
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="border border-border bg-card p-2 hover:border-foreground/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                data-testid="pagination-prev"
              >
                <ChevronLeft size={14} strokeWidth={1.5} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="border border-border bg-card p-2 hover:border-foreground/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                data-testid="pagination-next"
              >
                <ChevronRight size={14} strokeWidth={1.5} />
              </button>
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="runs-list-page">
      <div className="mb-8">
        <div className="text-label mb-2">Pipeline Activity</div>
        <h1 className="text-3xl sm:text-4xl tracking-tight font-semibold">Runs</h1>
      </div>

      {/* Filters */}
      <div className="border border-border bg-card p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-label">Source</span>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="bg-secondary border border-border px-3 py-1.5 text-xs font-mono uppercase tracking-wider focus:outline-none focus:border-foreground/50"
              data-testid="source-filter"
            >
              <option value="">All</option>
              {SOURCE_KEYS.map((key) => (
                <option key={key} value={key}>
                  {SOURCE_LABELS[key]}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-label">Status</span>
            <div className="flex border border-border">
              <button
                onClick={() => setStatusFilter("")}
                data-testid="status-filter-all"
                className={cn(
                  "px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors border-r border-border last:border-r-0",
                  statusFilter === "" ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
                )}
              >
                All
              </button>
              {STATUS_FILTERS.map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  data-testid={`status-filter-${s}`}
                  className={cn(
                    "px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors border-r border-border last:border-r-0",
                    statusFilter === s ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 uppercase tracking-wider font-medium"
              data-testid="clear-filters-button"
            >
              <X size={12} />
              Clear
            </button>
          )}

          <div className="ml-auto text-xs font-mono text-muted-foreground">
            {total} {total === 1 ? "run" : "runs"}
          </div>
        </div>
      </div>

      {renderContent()}
    </div>
  );
}

// ============ Run Detail Page ============
export function RunDetailPage() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    runsApi
      .get(runId)
      .then((data) => {
        if (isMounted) {
          setRun(data);
          // Restore prior AI analysis if exists
          if (data.ai_analysis) setAiAnalysis(data.ai_analysis);
        }
      })
      .catch(() => {
        if (isMounted) setError("Run not found");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [runId]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const result = await aiApi.analyzeRun(runId);
      setAiAnalysis(result);
    } catch (err) {
      setAiAnalysis({ root_cause: "Analysis failed", summary: err.message, recommendations: [] });
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border border-border bg-card h-64 flex items-center justify-center text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
          Loading run…
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border border-destructive/30 bg-destructive/5 p-8 text-center">
          <h2 className="text-xl font-semibold mb-2">Run not found</h2>
          <button
            onClick={() => navigate("/runs")}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to runs
          </button>
        </div>
      </div>
    );
  }

  const DetailRow = ({ label, children, mono = false }) => (
    <div className="flex items-baseline gap-4 py-2.5 border-b border-border last:border-0">
      <div className="text-label w-40 shrink-0">{label}</div>
      <div className={cn("flex-1 text-sm", mono && "font-mono text-xs")}>{children || <span className="text-muted-foreground">—</span>}</div>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="run-detail-page">
      {/* Breadcrumb */}
      <Link
        to="/runs"
        className="inline-flex items-center gap-2 text-xs uppercase tracking-wider font-medium text-muted-foreground hover:text-foreground mb-6"
        data-testid="back-to-runs-link"
      >
        <ArrowLeft size={12} strokeWidth={1.5} />
        Back to runs
      </Link>

      {/* Header */}
      <div className="border border-border bg-card p-6 mb-6">
        <div className="flex items-start gap-4 mb-4">
          <SourceIcon source={run.source} size={28} />
          <div className="flex-1 min-w-0">
            <div className="text-label mb-1">
              {SOURCE_LABELS[run.source]} · #{run.metadata?.run_number || run.external_id}
            </div>
            <h1 className="text-2xl tracking-tight font-semibold mb-2 break-words">{run.name}</h1>
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge status={run.status} />
              {run.external_url && (
                <a
                  href={run.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1 uppercase tracking-wider font-medium"
                  data-testid="external-link"
                >
                  View source <ExternalLink size={10} strokeWidth={1.5} />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-border mt-6">
          <div className="bg-card p-4">
            <div className="text-label mb-1">Duration</div>
            <div className="text-lg font-mono">{formatDuration(run.duration_seconds)}</div>
          </div>
          <div className="bg-card p-4">
            <div className="text-label mb-1">Started</div>
            <div className="text-sm font-mono">{run.started_at ? formatRelativeTime(run.started_at) : "—"}</div>
          </div>
          <div className="bg-card p-4">
            <div className="text-label mb-1">Completed</div>
            <div className="text-sm font-mono">{run.completed_at ? formatRelativeTime(run.completed_at) : "—"}</div>
          </div>
          <div className="bg-card p-4">
            <div className="text-label mb-1">Trigger</div>
            <div className="text-sm font-mono uppercase">{run.trigger || "—"}</div>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="border border-border bg-card p-6 mb-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider mb-4 text-muted-foreground">
          Details
        </h2>
        <div>
          <DetailRow label="Repository" mono>
            {run.repository}
          </DetailRow>
          <DetailRow label="Branch" mono>
            {run.branch && (
              <span className="inline-flex items-center gap-1.5">
                <GitBranch size={12} strokeWidth={1.5} />
                {run.branch}
              </span>
            )}
          </DetailRow>
          <DetailRow label="Commit" mono>
            {run.commit_sha && (
              <span className="inline-flex items-center gap-1.5">
                <GitCommit size={12} strokeWidth={1.5} />
                {shortSha(run.commit_sha)}
                <span className="text-muted-foreground">— {run.commit_message || "no message"}</span>
              </span>
            )}
          </DetailRow>
          <DetailRow label="Author">
            {run.author && (
              <span className="inline-flex items-center gap-1.5">
                <User size={12} strokeWidth={1.5} />
                {run.author}
              </span>
            )}
          </DetailRow>
          <DetailRow label="Conclusion" mono>
            {run.conclusion}
          </DetailRow>
          <DetailRow label="Started at" mono>
            {formatDateTime(run.started_at)}
          </DetailRow>
          <DetailRow label="Completed at" mono>
            {formatDateTime(run.completed_at)}
          </DetailRow>
          <DetailRow label="Run ID" mono>
            {run.id}
          </DetailRow>
        </div>
      </div>

      {/* Error message (if failed) */}
      {run.status === "failure" && (
        <div className="border border-destructive/30 bg-destructive/5 p-6 mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider mb-3 text-destructive flex items-center gap-2">
            <Clock size={14} strokeWidth={1.5} />
            Failure
          </h2>
          {run.error_message ? (
            <pre className="text-xs font-mono whitespace-pre-wrap text-foreground">{run.error_message}</pre>
          ) : (
            <p className="text-sm text-muted-foreground">
              No error message captured. Connect AI log summarization to get automated failure analysis.
            </p>
          )}
        </div>
      )}

      {/* AI Analysis */}
      <div className="border border-border bg-card p-6 mb-6" data-testid="ai-analysis-section">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Sparkles size={14} strokeWidth={1.5} className="text-[#F59E0B]" />
            AI Analysis
          </h2>
          {!aiAnalysis && !analyzing && (
            <button
              onClick={runAnalysis}
              className="border border-border hover:border-foreground/30 px-3 py-1.5 text-xs uppercase tracking-wider font-medium flex items-center gap-2 transition-colors"
              data-testid="run-ai-analysis-button"
            >
              <Sparkles size={12} strokeWidth={1.5} />
              Analyze with AI
            </button>
          )}
          {analyzing && (
            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Loader2 size={12} className="animate-spin" />
              Analyzing…
            </div>
          )}
        </div>

        {aiAnalysis ? (
          <div className="space-y-4" data-testid="ai-analysis-content">
            <div>
              <div className="text-label mb-2">Root cause</div>
              <p className="text-sm leading-relaxed">{aiAnalysis.root_cause || "—"}</p>
            </div>
            {aiAnalysis.summary && (
              <div>
                <div className="text-label mb-2">Summary</div>
                <p className="text-sm leading-relaxed text-muted-foreground">{aiAnalysis.summary}</p>
              </div>
            )}
            {aiAnalysis.recommendations && aiAnalysis.recommendations.length > 0 && (
              <div>
                <div className="text-label mb-2">Recommendations</div>
                <ul className="space-y-2">
                  {aiAnalysis.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm flex gap-2">
                      <span className="text-[#F59E0B] font-mono">{idx + 1}.</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="border border-dashed border-border p-6 text-center">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              Click "Analyze with AI" to get root cause analysis and recommendations
            </p>
          </div>
        )}
      </div>

      {/* Metadata */}
      {run.metadata && Object.keys(run.metadata).length > 0 && (
        <div className="border border-border bg-card p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider mb-4 text-muted-foreground">
            Metadata
          </h2>
          <pre className="text-xs font-mono text-foreground whitespace-pre-wrap bg-secondary/50 p-4 overflow-x-auto">
            {JSON.stringify(run.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
