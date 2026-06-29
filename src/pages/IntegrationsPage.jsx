import React, { useEffect, useState, useCallback } from "react";
import { pipelineApi, webhookApi } from "@/lib/api";
import { cn, formatRelativeTime, SOURCE_LABELS, SOURCE_KEYS } from "@/lib/utils";
import { SourceIcon } from "@/components/SourceIcon";
import { toast } from "sonner";
import {
  Plus, Loader2, X, Zap, Check, Copy, BookOpen, Trash2, RefreshCw,
  Webhook, Download, ExternalLink, ChevronRight,
} from "lucide-react";

// ---------- helpers ----------
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
    return true;
  } catch {
    toast.error("Copy failed — select & copy manually");
    return false;
  }
}

const PULL_SUPPORTED = new Set(["github", "gitlab", "jenkins"]);

// =========================================================================
// Main page
// =========================================================================
export function IntegrationsPage() {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [guideFor, setGuideFor] = useState(null);
  const [simulating, setSimulating] = useState(null);
  const [syncing, setSyncing] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await pipelineApi.listIntegrations();
      setIntegrations(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete integration "${name}"? Existing runs will be kept.`)) return;
    try {
      await pipelineApi.deleteIntegration(id);
      toast.success(`Removed ${name}`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleSync = async (integration) => {
    setSyncing(integration.id);
    try {
      const r = await pipelineApi.syncNow(integration.id);
      if (r.ok) toast.success(`${integration.name}: ingested ${r.ingested} run(s)`);
      else toast.error(`${integration.name}: ${r.reason || "Sync failed"}`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Sync failed");
    } finally {
      setSyncing(null);
    }
  };

  const handleSimulate = async (source) => {
    setSimulating(source);
    try {
      const samples = buildSampleEvents();
      const sample = samples[source];
      if (!sample) {
        toast.info(`Simulator for ${source} coming soon`);
        return;
      }
      if (source === "github") await webhookApi.github(sample.payload, sample.eventType);
      else if (source === "gitlab") await webhookApi.gitlab(sample.payload);
      else if (source === "jenkins") await webhookApi.jenkins(sample.payload);
      toast.success("Test event sent — check Live Pipelines!");
    } catch (err) {
      toast.error(err.message || "Failed to send test event");
    } finally {
      setSimulating(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="integrations-page">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold mb-2">Connections</div>
          <h1 className="text-3xl sm:text-4xl tracking-tight font-bold text-slate-900">Integrations</h1>
          <p className="text-sm text-slate-500 mt-1 max-w-xl">
            Connect GitHub Actions, Jenkins, GitLab CI and more. Use webhooks for instant streaming or pull mode for systems behind a firewall.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2.5 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white text-xs font-semibold uppercase tracking-wider flex items-center gap-2 hover:shadow-lg hover:shadow-indigo-500/30 transition-all"
          data-testid="add-integration-button"
        >
          <Plus size={14} strokeWidth={2.5} />
          Add Integration
        </button>
      </div>

      {/* Connected list */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">Connected</h2>
        {loading && <div className="glass-card rounded-2xl h-24 flex items-center justify-center text-xs text-slate-400 font-mono uppercase tracking-wider">Loading…</div>}
        {!loading && integrations.length === 0 && (
          <div className="glass-card rounded-2xl border-2 border-dashed border-slate-200 p-10 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-3 shadow-lg shadow-indigo-500/30">
              <Webhook size={22} className="text-white" strokeWidth={2} />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-1">No integrations yet</h3>
            <p className="text-sm text-slate-500 mb-4 max-w-md mx-auto">
              Add a CI/CD platform to start receiving pipeline events. Setup takes ~2 minutes per platform.
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 rounded-full bg-slate-900 text-white text-xs font-semibold uppercase tracking-wider hover:bg-slate-800"
            >
              Connect your first platform →
            </button>
          </div>
        )}
        {!loading && integrations.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="integrations-list">
            {integrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onGuide={() => setGuideFor(integration)}
                onDelete={() => handleDelete(integration.id, integration.name)}
                onSync={() => handleSync(integration)}
                onSimulate={() => handleSimulate(integration.type)}
                syncing={syncing === integration.id}
                simulating={simulating === integration.type}
              />
            ))}
          </div>
        )}
      </section>

      {/* Available platforms */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">All supported platforms</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {SOURCE_KEYS.map((source) => {
            const connected = integrations.some((i) => i.type === source);
            return (
              <button
                key={source}
                onClick={() => { setShowAddModal(true); }}
                className={cn(
                  "glass-card rounded-2xl p-4 text-left transition-all hover:shadow-md",
                  connected ? "border-emerald-200" : "hover:border-indigo-300",
                )}
                data-testid={`platform-${source}`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center">
                    <SourceIcon source={source} size={22} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-800 truncate">{SOURCE_LABELS[source]}</div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
                      {connected ? "Connected" : PULL_SUPPORTED.has(source) ? "Webhook · Pull" : "Webhook"}
                    </div>
                  </div>
                </div>
                {connected ? (
                  <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold uppercase tracking-wider">
                    <Check size={10} strokeWidth={3} /> Connected
                  </div>
                ) : (
                  <div className="text-[11px] text-slate-500 inline-flex items-center gap-1 group-hover:text-indigo-600">
                    Connect <ChevronRight size={11} strokeWidth={2} />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </section>

      {showAddModal && (
        <AddIntegrationModal
          onClose={() => setShowAddModal(false)}
          onSuccess={(newIntegration) => {
            setShowAddModal(false);
            load().then(() => {
              if (newIntegration) setGuideFor(newIntegration);
            });
          }}
        />
      )}

      {guideFor && (
        <SetupGuideModal integration={guideFor} onClose={() => setGuideFor(null)} />
      )}
    </div>
  );
}

// =========================================================================
// Integration card
// =========================================================================
function IntegrationCard({ integration, onGuide, onDelete, onSync, onSimulate, syncing, simulating }) {
  const cfg = integration.config || {};
  const mode = cfg.connection_mode || "webhook";
  const isPull = mode === "pull";
  return (
    <div className="glass-card rounded-2xl p-5" data-testid={`integration-${integration.id}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-slate-50 flex items-center justify-center">
            <SourceIcon source={integration.type} size={22} />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">{integration.name}</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">{SOURCE_LABELS[integration.type]}</div>
          </div>
        </div>
        <button
          onClick={onDelete}
          className="p-1.5 rounded-full hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
          title="Delete integration"
          data-testid={`delete-integration-${integration.id}`}
        >
          <Trash2 size={13} strokeWidth={2} />
        </button>
      </div>

      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border",
          isPull
            ? "bg-amber-50 text-amber-700 border-amber-200"
            : "bg-emerald-50 text-emerald-700 border-emerald-200",
        )}>
          {isPull ? <Download size={9} strokeWidth={3} /> : <Webhook size={9} strokeWidth={3} />}
          {isPull ? "Pull mode" : "Webhook mode"}
        </span>
        <span className="text-[10px] text-slate-400 font-mono">
          {formatRelativeTime(integration.created_at)}
        </span>
      </div>

      {isPull && cfg.last_synced_at && (
        <div className="text-[10px] text-slate-500 font-mono mb-3">
          Last synced {formatRelativeTime(cfg.last_synced_at)}
          {typeof cfg.last_sync_count === "number" && ` · ${cfg.last_sync_count} runs`}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={onGuide}
          className="flex-1 px-3 py-2 rounded-full bg-white/80 border border-slate-200 text-slate-700 text-[11px] font-semibold uppercase tracking-wider hover:bg-white hover:border-indigo-300 transition-colors inline-flex items-center justify-center gap-1.5"
          data-testid={`guide-${integration.id}`}
        >
          <BookOpen size={11} strokeWidth={2.5} />
          Setup guide
        </button>
        {isPull ? (
          <button
            onClick={onSync}
            disabled={syncing}
            className="flex-1 px-3 py-2 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-[11px] font-semibold uppercase tracking-wider hover:bg-amber-100 transition-colors inline-flex items-center justify-center gap-1.5 disabled:opacity-50"
            data-testid={`sync-${integration.id}`}
          >
            {syncing ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} strokeWidth={2.5} />}
            {syncing ? "Syncing…" : "Sync now"}
          </button>
        ) : (
          <button
            onClick={onSimulate}
            disabled={simulating}
            className="flex-1 px-3 py-2 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-[11px] font-semibold uppercase tracking-wider hover:bg-indigo-100 transition-colors inline-flex items-center justify-center gap-1.5 disabled:opacity-50"
            data-testid={`simulate-${integration.id}`}
          >
            {simulating ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} strokeWidth={2.5} />}
            {simulating ? "Sending…" : "Send test"}
          </button>
        )}
      </div>
    </div>
  );
}

// =========================================================================
// Setup-guide modal
// =========================================================================
function SetupGuideModal({ integration, onClose }) {
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    pipelineApi.setupGuide(integration.id)
      .then((g) => { if (!cancelled) { setGuide(g); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [integration.id]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
      data-testid="setup-guide-modal"
    >
      <div
        className="w-full max-w-3xl glass-card rounded-3xl p-6 sm:p-8 my-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center">
              <SourceIcon source={integration.type} size={26} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-indigo-600 font-bold">Setup guide</div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">{guide?.title || integration.name}</h2>
              {guide?.summary && (
                <p className="text-sm text-slate-500 mt-1 max-w-xl">{guide.summary}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 text-slate-500"
            data-testid="setup-guide-close"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        {loading && (
          <div className="h-40 flex items-center justify-center text-xs text-slate-400 font-mono uppercase tracking-wider">
            <Loader2 size={14} className="animate-spin mr-2" /> Loading guide…
          </div>
        )}

        {!loading && guide && (
          <div className="space-y-5">
            {guide.steps.map((step, idx) => (
              <div key={idx} className="relative pl-8" data-testid={`setup-step-${idx}`}>
                <div className="absolute left-0 top-0 w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-[11px] font-bold flex items-center justify-center shadow-lg shadow-indigo-500/30">
                  {idx + 1}
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-1">{step.title}</h4>
                  {step.body && <p className="text-sm text-slate-600 leading-relaxed mb-2">{step.body}</p>}
                  {step.code && (
                    <div className="relative group">
                      <pre className="bg-slate-900 text-slate-100 rounded-xl p-3 pr-12 text-[11px] font-mono overflow-x-auto whitespace-pre">
                        {step.code}
                      </pre>
                      <button
                        onClick={() => copyToClipboard(step.code)}
                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 transition-colors"
                        title="Copy"
                        data-testid={`copy-step-${idx}`}
                      >
                        <Copy size={12} strokeWidth={2} />
                      </button>
                    </div>
                  )}
                  {step.link && (
                    <a
                      href={step.link}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 mt-2 text-xs text-indigo-600 hover:text-indigo-700 font-semibold"
                    >
                      Official docs <ExternalLink size={11} strokeWidth={2.5} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 pt-4 border-t border-slate-200 flex items-center justify-between">
          <div className="text-[11px] text-slate-500">
            Need help? <a href="mailto:support@sparkcurv.com" className="text-indigo-600 font-semibold">Contact support</a>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-full bg-slate-900 text-white text-xs font-semibold uppercase tracking-wider hover:bg-slate-800"
            data-testid="setup-guide-done"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

// =========================================================================
// Add-integration modal (webhook OR pull mode)
// =========================================================================
function AddIntegrationModal({ onClose, onSuccess }) {
  const [type, setType] = useState("github");
  const [mode, setMode] = useState("webhook");
  const [name, setName] = useState("");
  const [token, setToken] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [username, setUsername] = useState("");
  const [repositories, setRepositories] = useState(""); // for github (csv) / gitlab (project ids csv) / jenkins (jobs csv)
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const pullEnabled = PULL_SUPPORTED.has(type);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const list = repositories.split(",").map((s) => s.trim()).filter(Boolean);
      const config = { connection_mode: mode, webhook_secret: cryptoRandomId() };
      if (mode === "pull") {
        config.api_token = token;
        if (type === "github") {
          if (list.length === 0) throw new Error("Add at least one repository (owner/repo)");
          config.repositories = list;
        } else if (type === "gitlab") {
          if (list.length === 0) throw new Error("Add at least one project (numeric ID or namespace/project)");
          config.project_ids = list;
          config.base_url = baseUrl || "https://gitlab.com";
        } else if (type === "jenkins") {
          if (!baseUrl || !username) throw new Error("Jenkins base URL and username are required");
          if (list.length === 0) throw new Error("Add at least one job name (or folder/job path)");
          config.base_url = baseUrl;
          config.username = username;
          config.jobs = list;
        }
      }
      const created = await pipelineApi.createIntegration({
        type,
        name: name || SOURCE_LABELS[type],
        config,
      });
      toast.success(`${created.name} connected`);
      onSuccess(created);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to create integration");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
      data-testid="add-integration-modal"
    >
      <div
        className="w-full max-w-2xl glass-card rounded-3xl p-6 sm:p-8 my-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-indigo-600 font-bold mb-1">New connection</div>
            <h2 className="text-2xl font-bold text-slate-900">Add Integration</h2>
            <p className="text-sm text-slate-500 mt-1">Choose a platform and pick how Pipelynx should receive data.</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 text-slate-500" data-testid="modal-close">
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" data-testid="add-integration-form">
          {/* Platform */}
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Platform</label>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
              {SOURCE_KEYS.map((src) => (
                <button
                  key={src}
                  type="button"
                  onClick={() => {
                    setType(src);
                    if (!PULL_SUPPORTED.has(src)) setMode("webhook");
                  }}
                  className={cn(
                    "rounded-2xl p-3 flex flex-col items-center gap-2 transition-all border-2",
                    type === src
                      ? "border-indigo-500 bg-indigo-50 shadow-md shadow-indigo-500/10"
                      : "border-slate-200 bg-white/70 hover:border-indigo-300",
                  )}
                  data-testid={`modal-platform-${src}`}
                >
                  <SourceIcon source={src} size={22} />
                  <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-700">{src}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Mode toggle */}
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Connection mode</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setMode("webhook")}
                className={cn(
                  "rounded-2xl p-3 text-left border-2 transition-all",
                  mode === "webhook" ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-white/70 hover:border-indigo-300",
                )}
                data-testid="mode-webhook"
              >
                <div className="flex items-center gap-2 mb-1">
                  <Webhook size={14} strokeWidth={2.5} className="text-indigo-600" />
                  <span className="text-sm font-semibold text-slate-800">Webhook</span>
                </div>
                <p className="text-[11px] text-slate-500">Push-based. Real-time. Recommended.</p>
              </button>
              <button
                type="button"
                onClick={() => pullEnabled && setMode("pull")}
                disabled={!pullEnabled}
                className={cn(
                  "rounded-2xl p-3 text-left border-2 transition-all",
                  mode === "pull" ? "border-amber-500 bg-amber-50" : "border-slate-200 bg-white/70 hover:border-amber-300",
                  !pullEnabled && "opacity-40 cursor-not-allowed",
                )}
                data-testid="mode-pull"
              >
                <div className="flex items-center gap-2 mb-1">
                  <Download size={14} strokeWidth={2.5} className="text-amber-600" />
                  <span className="text-sm font-semibold text-slate-800">Pull (API token)</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  {pullEnabled ? "Polls the API every 60s. Use behind a firewall." : "Not supported for this platform"}
                </p>
              </button>
            </div>
          </div>

          {/* Name */}
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={SOURCE_LABELS[type]}
              className="w-full bg-white/80 border-2 border-slate-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-indigo-500"
              data-testid="modal-name-input"
            />
          </div>

          {/* Pull-mode fields */}
          {mode === "pull" && (
            <div className="space-y-3 rounded-2xl bg-amber-50/60 border-2 border-amber-200 p-4">
              <div className="text-[10px] uppercase tracking-widest text-amber-700 font-bold">Pull mode credentials</div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1.5">API token / PAT</label>
                <input
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                  placeholder={
                    type === "github" ? "ghp_… (repo + actions:read scope)" :
                    type === "gitlab" ? "glpat-… (read_api scope)" :
                    "Jenkins API token"
                  }
                  className="w-full bg-white border-2 border-amber-200 rounded-xl px-3 py-2 text-sm font-mono focus:outline-none focus:border-amber-500"
                  data-testid="pull-token-input"
                />
              </div>

              {(type === "gitlab" || type === "jenkins") && (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1.5">
                    {type === "gitlab" ? "Base URL (gitlab.com or self-hosted)" : "Jenkins base URL"}
                  </label>
                  <input
                    type="url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    required={type === "jenkins"}
                    placeholder={type === "gitlab" ? "https://gitlab.com" : "https://jenkins.your-company.com"}
                    className="w-full bg-white border-2 border-amber-200 rounded-xl px-3 py-2 text-sm font-mono focus:outline-none focus:border-amber-500"
                    data-testid="pull-base-url-input"
                  />
                </div>
              )}

              {type === "jenkins" && (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1.5">Jenkins username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    placeholder="ci-bot"
                    className="w-full bg-white border-2 border-amber-200 rounded-xl px-3 py-2 text-sm font-mono focus:outline-none focus:border-amber-500"
                    data-testid="pull-username-input"
                  />
                </div>
              )}

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1.5">
                  {type === "github" && "Repositories (comma-separated, owner/repo)"}
                  {type === "gitlab" && "Project IDs or paths (comma-separated)"}
                  {type === "jenkins" && "Job names (comma-separated, supports folder/job/sub)"}
                </label>
                <input
                  type="text"
                  value={repositories}
                  onChange={(e) => setRepositories(e.target.value)}
                  required
                  placeholder={
                    type === "github" ? "octocat/hello-world, octocat/api-server" :
                    type === "gitlab" ? "12345, mygroup/api-service" :
                    "deploy-prod, mobile/build-ios"
                  }
                  className="w-full bg-white border-2 border-amber-200 rounded-xl px-3 py-2 text-sm font-mono focus:outline-none focus:border-amber-500"
                  data-testid="pull-targets-input"
                />
              </div>
              <p className="text-[10px] text-amber-700">
                Pipelynx will poll every 60s and ingest new runs as they appear.
              </p>
            </div>
          )}

          {/* Webhook mode info */}
          {mode === "webhook" && (
            <div className="rounded-2xl bg-indigo-50/60 border-2 border-indigo-200 p-4">
              <div className="flex items-start gap-3">
                <Webhook size={18} className="text-indigo-600 flex-shrink-0 mt-0.5" strokeWidth={2.5} />
                <div className="text-[11px] text-slate-700">
                  After creating the integration, Pipelynx will show you a step-by-step setup guide with the webhook URL, secret, and exact configuration for {SOURCE_LABELS[type]}.
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-xl border-2 border-rose-200 bg-rose-50 text-rose-700 text-xs px-3 py-2 font-mono">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-full text-xs font-semibold uppercase tracking-wider text-slate-600 hover:text-slate-900"
              data-testid="modal-cancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white text-xs font-semibold uppercase tracking-wider hover:shadow-lg hover:shadow-indigo-500/30 inline-flex items-center gap-2 disabled:opacity-50"
              data-testid="modal-submit"
            >
              {loading ? <Loader2 size={12} className="animate-spin" /> : null}
              {loading ? "Connecting…" : "Connect →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------- sample webhook events ----------
function buildSampleEvents() {
  return {
    github: {
      eventType: "workflow_run",
      payload: {
        workflow_run: {
          id: Math.floor(Math.random() * 1e10),
          name: "Build & Deploy",
          status: "completed",
          conclusion: Math.random() > 0.3 ? "success" : "failure",
          run_number: Math.floor(Math.random() * 1000),
          run_attempt: 1,
          html_url: "https://github.com/sample/repo/actions/runs/123",
          run_started_at: new Date(Date.now() - 300000).toISOString(),
          updated_at: new Date().toISOString(),
          head_branch: ["main", "develop", "feature/new-ui"][Math.floor(Math.random() * 3)],
          head_sha: Math.random().toString(36).substring(2, 18),
          event: "push",
          workflow_id: 99,
          head_commit: { message: "chore: simulated event" },
          triggering_actor: { login: "demo-user" },
        },
        repository: { full_name: "sparkcurv/demo-repo" },
      },
    },
    gitlab: {
      payload: {
        object_kind: "pipeline",
        object_attributes: {
          id: Math.floor(Math.random() * 1e6),
          status: Math.random() > 0.4 ? "success" : "failed",
          ref: "main",
          sha: Math.random().toString(36).substring(2, 18),
          source: "push",
          duration: Math.floor(Math.random() * 600) + 60,
          created_at: new Date(Date.now() - 360000).toISOString(),
          finished_at: new Date().toISOString(),
          url: "https://gitlab.com/sample/-/pipelines/1",
        },
        project: { path_with_namespace: "sparkcurv/api" },
        commit: { id: "abc123", message: "feat: simulated GitLab event" },
        user: { username: "demo-user" },
      },
    },
    jenkins: {
      payload: {
        name: "demo-build",
        build: {
          number: Math.floor(Math.random() * 1000),
          phase: "COMPLETED",
          status: Math.random() > 0.5 ? "SUCCESS" : "FAILURE",
          timestamp: Date.now() - 240000,
          duration: Math.floor(Math.random() * 300000) + 60000,
          full_url: "https://jenkins.demo/job/demo/1/",
          scm: { branch: "main", commit: Math.random().toString(36).substring(2, 18) },
        },
      },
    },
  };
}

function cryptoRandomId() {
  try {
    const arr = new Uint8Array(16);
    window.crypto.getRandomValues(arr);
    return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
  } catch {
    return Math.random().toString(36).slice(2);
  }
}
