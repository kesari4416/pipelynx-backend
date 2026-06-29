import React, { useEffect, useState, useCallback } from "react";
import { alertsApi } from "@/lib/api";
import { cn, formatRelativeTime, SOURCE_LABELS, SOURCE_KEYS } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { SourceIcon } from "@/components/SourceIcon";
import { Bell, Plus, Trash2, X, Loader2, Check, Slack, Mail, Webhook as WebhookIcon, Send } from "lucide-react";

const STATUSES = ["success", "failure", "running", "queued", "cancelled", "skipped"];
const CHANNELS = [
  { id: "slack", label: "Slack", icon: Slack },
  { id: "email", label: "Email", icon: Mail },
  { id: "webhook", label: "Webhook", icon: WebhookIcon },
];

export function AlertsPage() {
  const [rules, setRules] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState("rules");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, historyData] = await Promise.all([
        alertsApi.listRules(),
        alertsApi.history(50),
      ]);
      setRules(rulesData);
      setHistory(historyData.alerts || []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this alert rule?")) return;
    await alertsApi.deleteRule(id);
    load();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="alerts-page">
      <div className="flex items-end justify-between mb-8">
        <div>
          <div className="text-label mb-2 flex items-center gap-2">
            <Bell size={12} strokeWidth={1.5} />
            Notifications
          </div>
          <h1 className="text-3xl sm:text-4xl tracking-tight font-semibold">Alerts</h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-foreground text-background px-4 py-2 text-xs uppercase tracking-wider font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
          data-testid="create-rule-button"
        >
          <Plus size={14} strokeWidth={1.5} />
          New Rule
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6" data-testid="alerts-tabs">
        {[
          { id: "rules", label: `Rules (${rules.length})` },
          { id: "history", label: `History (${history.length})` },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "px-4 py-2 text-xs uppercase tracking-wider font-medium border-b-2 -mb-px transition-colors",
              tab === t.id
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
            data-testid={`tab-${t.id}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Rules tab */}
      {tab === "rules" && (
        <RulesTab loading={loading} rules={rules} onDelete={handleDelete} />
      )}

      {/* History tab */}
      {tab === "history" && (
        <HistoryTab loading={loading} history={history} />
      )}

      {showCreate && (
        <CreateRuleModal
          onClose={() => setShowCreate(false)}
          onSuccess={() => {
            setShowCreate(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function RulesTab({ loading, rules, onDelete }) {
  if (loading) {
    return (
      <div className="border border-border bg-card h-32 flex items-center justify-center text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
        Loading rules…
      </div>
    );
  }
  if (rules.length === 0) {
    return (
      <div className="border border-dashed border-border p-12 text-center">
        <Bell size={24} className="mx-auto text-muted-foreground mb-4" strokeWidth={1.5} />
        <h3 className="text-lg font-semibold mb-2">No alert rules</h3>
        <p className="text-sm text-muted-foreground">
          Create a rule to get notified when pipeline conditions are met.
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-3" data-testid="rules-list">
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="border border-border bg-card p-5 flex items-center justify-between"
          data-testid={`rule-${rule.id}`}
        >
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <Bell size={14} strokeWidth={1.5} className="text-[#F59E0B]" />
              <h3 className="text-sm font-medium">{rule.name}</h3>
              {rule.is_active && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 border border-[#2ECC71]/30 bg-[#2ECC71]/10 text-[#2ECC71] font-mono text-[10px] uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#2ECC71]" />
                  Active
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-3 text-xs font-mono text-muted-foreground">
              {Object.entries(rule.condition || {}).map(([k, v]) => (
                <span key={k}>
                  <span className="text-foreground">{k}</span>=
                  <span>{Array.isArray(v) ? v.join("|") : String(v)}</span>
                </span>
              ))}
            </div>
            <div className="flex gap-1.5 mt-2">
              {(rule.channels || []).map((ch) => {
                const def = CHANNELS.find((c) => c.id === ch);
                const Icon = def?.icon || Bell;
                return (
                  <span
                    key={ch}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-secondary text-muted-foreground text-[10px] uppercase tracking-wider font-mono"
                  >
                    <Icon size={10} strokeWidth={1.5} />
                    {ch}
                  </span>
                );
              })}
            </div>
          </div>
          <button
            onClick={() => onDelete(rule.id)}
            className="p-2 text-muted-foreground hover:text-destructive transition-colors"
            data-testid={`delete-rule-${rule.id}`}
            title="Delete rule"
          >
            <Trash2 size={14} strokeWidth={1.5} />
          </button>
        </div>
      ))}
    </div>
  );
}

function HistoryTab({ loading, history }) {
  if (loading) return <div className="text-muted-foreground font-mono text-xs uppercase tracking-wider">Loading…</div>;
  if (history.length === 0) {
    return (
      <div className="border border-dashed border-border p-12 text-center">
        <Bell size={24} className="mx-auto text-muted-foreground mb-4" strokeWidth={1.5} />
        <h3 className="text-lg font-semibold mb-2">No alerts triggered yet</h3>
        <p className="text-sm text-muted-foreground">
          When your rules match incoming pipeline events, they'll appear here.
        </p>
      </div>
    );
  }
  return (
    <div className="border border-border bg-card divide-y divide-border" data-testid="alert-history-list">
      {history.map((alert) => (
        <div key={alert.id} className="p-4 flex items-center gap-4" data-testid={`alert-${alert.id}`}>
          <Bell size={14} strokeWidth={1.5} className="text-[#F59E0B] shrink-0" />
          <StatusBadge status={alert.run?.status} />
          <SourceIcon source={alert.run?.source} size={14} />
          <div className="flex-1 min-w-0">
            <div className="text-sm truncate">{alert.run?.name}</div>
            <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider truncate">
              {alert.rule_name} · {alert.run?.repository || "—"}
            </div>
          </div>
          <div className="text-xs font-mono text-muted-foreground">
            {formatRelativeTime(alert.triggered_at)}
          </div>
        </div>
      ))}
    </div>
  );
}

function CreateRuleModal({ onClose, onSuccess }) {
  const [name, setName] = useState("");
  const [statusFilter, setStatusFilter] = useState("failure");
  const [sourceFilter, setSourceFilter] = useState("");
  const [branchFilter, setBranchFilter] = useState("");
  const [channel, setChannel] = useState("email");
  const [slackUrl, setSlackUrl] = useState("");
  const [emailRecipients, setEmailRecipients] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState("");

  const buildChannelConfig = () => {
    if (channel === "slack") return { webhook_url: slackUrl };
    if (channel === "email") return { recipients: emailRecipients.split(",").map((s) => s.trim()).filter(Boolean) };
    if (channel === "webhook") return { url: webhookUrl };
    return {};
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await alertsApi.test(channel, buildChannelConfig());
      setTestResult({ ok: result.success, message: result.success ? "Test sent successfully!" : "Test failed" });
    } catch (err) {
      setTestResult({ ok: false, message: err.response?.data?.detail || err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const condition = {};
      if (statusFilter) condition.status = statusFilter;
      if (sourceFilter) condition.source = sourceFilter;
      if (branchFilter) condition.branch = branchFilter;
      
      await alertsApi.createRule({
        name: name || `Alert on ${statusFilter}`,
        condition,
        channels: [channel],
        channel_configs: { [channel]: buildChannelConfig() },
        is_active: true,
      });
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create rule");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl border border-border bg-card p-6 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-label mb-1">New alert</div>
            <h2 className="text-xl tracking-tight font-semibold">Create Alert Rule</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/[0.06] transition-colors text-muted-foreground hover:text-foreground">
            <X size={16} strokeWidth={1.5} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" data-testid="create-rule-form">
          {/* Name */}
          <div>
            <label className="block text-label mb-2">Rule name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Production failures"
              className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:border-foreground/50"
              data-testid="rule-name-input"
            />
          </div>

          {/* Conditions */}
          <div>
            <label className="block text-label mb-2">Trigger when</label>
            <div className="space-y-3 border border-border bg-secondary/50 p-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-muted-foreground w-16">Status</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="flex-1 bg-secondary border border-border px-3 py-1.5 text-xs font-mono uppercase tracking-wider"
                >
                  <option value="">Any</option>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-muted-foreground w-16">Source</span>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="flex-1 bg-secondary border border-border px-3 py-1.5 text-xs font-mono uppercase tracking-wider"
                >
                  <option value="">Any</option>
                  {SOURCE_KEYS.map((s) => (
                    <option key={s} value={s}>{SOURCE_LABELS[s]}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-muted-foreground w-16">Branch</span>
                <input
                  type="text"
                  value={branchFilter}
                  onChange={(e) => setBranchFilter(e.target.value)}
                  placeholder="(optional, e.g. main)"
                  className="flex-1 bg-secondary border border-border px-3 py-1.5 text-xs font-mono"
                />
              </div>
            </div>
          </div>

          {/* Channel */}
          <div>
            <label className="block text-label mb-2">Notify via</label>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {CHANNELS.map((ch) => {
                const Icon = ch.icon;
                return (
                  <button
                    key={ch.id}
                    type="button"
                    onClick={() => setChannel(ch.id)}
                    className={cn(
                      "border bg-secondary p-3 flex flex-col items-center gap-2 transition-colors",
                      channel === ch.id ? "border-foreground" : "border-border hover:border-foreground/30"
                    )}
                    data-testid={`channel-${ch.id}`}
                  >
                    <Icon size={18} strokeWidth={1.5} />
                    <span className="text-[10px] uppercase tracking-wider">{ch.label}</span>
                  </button>
                );
              })}
            </div>

            {channel === "slack" && (
              <input
                type="text"
                value={slackUrl}
                onChange={(e) => setSlackUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:border-foreground/50"
                data-testid="slack-url-input"
              />
            )}
            {channel === "email" && (
              <input
                type="text"
                value={emailRecipients}
                onChange={(e) => setEmailRecipients(e.target.value)}
                placeholder="alerts@yourcompany.com, oncall@yourcompany.com"
                className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:border-foreground/50"
                data-testid="email-recipients-input"
              />
            )}
            {channel === "webhook" && (
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://your-service.com/webhooks/alerts"
                className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:border-foreground/50"
                data-testid="webhook-url-input"
              />
            )}

            {/* Test button */}
            <div className="mt-3 flex items-center gap-2">
              <button
                type="button"
                onClick={handleTest}
                disabled={testing}
                className="border border-border px-3 py-1.5 text-xs uppercase tracking-wider font-medium hover:border-foreground/30 transition-colors flex items-center gap-2 disabled:opacity-50"
                data-testid="test-channel-button"
              >
                {testing ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} strokeWidth={1.5} />}
                Send test
              </button>
              {testResult && (
                <span
                  className={cn(
                    "text-xs font-mono flex items-center gap-1",
                    testResult.ok ? "text-[#2ECC71]" : "text-destructive"
                  )}
                >
                  {testResult.ok ? <Check size={12} /> : <X size={12} />}
                  {testResult.message}
                </span>
              )}
            </div>
          </div>

          {error && (
            <div className="border border-destructive/30 bg-destructive/10 text-destructive text-xs font-mono px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs uppercase tracking-wider font-medium text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-foreground text-background px-4 py-2 text-xs uppercase tracking-wider font-medium hover:opacity-90 transition-opacity flex items-center gap-2 disabled:opacity-50"
              data-testid="submit-rule"
            >
              {loading ? <Loader2 size={12} className="animate-spin" /> : null}
              Create rule →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
