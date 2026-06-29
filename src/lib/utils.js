// Utility functions for formatting and display
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Format duration in seconds to human-readable
export function formatDuration(seconds) {
  if (seconds == null || isNaN(seconds)) return "—";
  const s = Number(seconds);
  if (s < 60) return `${s.toFixed(0)}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

// Format relative time
export function formatRelativeTime(dateString) {
  if (!dateString) return "—";
  const d = new Date(dateString);
  const now = new Date();
  const diff = now - d;
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return d.toLocaleDateString();
}

// Format absolute date
export function formatDateTime(dateString) {
  if (!dateString) return "—";
  return new Date(dateString).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Short commit SHA
export function shortSha(sha) {
  if (!sha) return "—";
  return sha.substring(0, 7);
}

// Status color mapping (matches design_guidelines)
export const STATUS_STYLES = {
  success: "text-[#2ECC71] bg-[#2ECC71]/10 border-[#2ECC71]/30",
  failure: "text-[#FF3B30] bg-[#FF3B30]/10 border-[#FF3B30]/30",
  running: "text-[#3B82F6] bg-[#3B82F6]/10 border-[#3B82F6]/30",
  queued: "text-[#F59E0B] bg-[#F59E0B]/10 border-[#F59E0B]/30",
  cancelled: "text-[#A1A1AA] bg-[#A1A1AA]/10 border-[#A1A1AA]/30",
  skipped: "text-[#78716C] bg-[#78716C]/10 border-[#78716C]/30",
};

export const STATUS_DOT_COLORS = {
  success: "bg-[#2ECC71]",
  failure: "bg-[#FF3B30]",
  running: "bg-[#3B82F6]",
  queued: "bg-[#F59E0B]",
  cancelled: "bg-[#A1A1AA]",
  skipped: "bg-[#78716C]",
};

// CI/CD source labels
export const SOURCE_LABELS = {
  github: "GitHub Actions",
  gitlab: "GitLab CI",
  jenkins: "Jenkins",
  circleci: "CircleCI",
  argocd: "ArgoCD",
  aws: "AWS CodePipeline",
  bitbucket: "Bitbucket",
};

export const SOURCE_KEYS = Object.keys(SOURCE_LABELS);
