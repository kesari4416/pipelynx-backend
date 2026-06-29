import React from "react";
import { cn } from "@/lib/utils";

/**
 * Pipelynx Logo - Geometric SVG (two overlapping diamonds = connected pipelines)
 */
export function Logo({ className = "", showText = true, size = "md" }) {
  const dimensions = {
    sm: { icon: 18, text: "text-base" },
    md: { icon: 22, text: "text-lg" },
    lg: { icon: 32, text: "text-2xl" },
  };
  const d = dimensions[size] || dimensions.md;

  return (
    <div className={cn("flex items-center gap-2.5 select-none", className)} data-testid="pipelynx-logo">
      <svg
        width={d.icon}
        height={d.icon}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Pipelynx logo"
      >
        {/* Two interlocked diamonds — pipeline + node */}
        <path
          d="M12 2 L22 12 L12 22 L2 12 Z"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M12 7 L17 12 L12 17 L7 12 Z"
          fill="currentColor"
        />
      </svg>
      {showText && (
        <span className={cn("font-semibold tracking-tight text-foreground", d.text)}>
          pipelynx
        </span>
      )}
    </div>
  );
}
