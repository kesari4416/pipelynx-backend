import React from "react";
import { cn } from "@/lib/utils";
import { STATUS_STYLES, STATUS_DOT_COLORS } from "@/lib/utils";

/**
 * Status badge for pipeline runs
 * Pulses for "running" status
 */
export function StatusBadge({ status, className = "", showDot = true }) {
  const normalized = (status || "unknown").toLowerCase();
  const styles = STATUS_STYLES[normalized] || STATUS_STYLES.cancelled;
  const dotColor = STATUS_DOT_COLORS[normalized] || STATUS_DOT_COLORS.cancelled;
  const isRunning = normalized === "running";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 border font-mono text-[10px] uppercase tracking-wider",
        styles,
        className
      )}
      data-testid={`status-badge-${normalized}`}
    >
      {showDot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            dotColor,
            isRunning && "animate-status-pulse"
          )}
        />
      )}
      {normalized}
    </span>
  );
}
