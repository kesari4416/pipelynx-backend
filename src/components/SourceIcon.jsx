import React from "react";
import {
  SiGithubactions,
  SiGitlab,
  SiJenkins,
  SiCircleci,
  SiArgo,
  SiBitbucket,
} from "react-icons/si";
import { Cloud } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * AWS icon - using lucide Cloud as fallback since react-icons changed naming.
 */
function AWSIcon({ size, className }) {
  return (
    <div
      className={cn("inline-flex items-center justify-center font-mono font-semibold", className)}
      style={{ width: size, height: size, fontSize: size * 0.45 }}
    >
      <span style={{ color: "#FF9900" }}>AWS</span>
    </div>
  );
}

const SOURCE_ICONS = {
  github: SiGithubactions,
  gitlab: SiGitlab,
  jenkins: SiJenkins,
  circleci: SiCircleci,
  argocd: SiArgo,
  aws: AWSIcon,
  bitbucket: SiBitbucket,
};

const SOURCE_COLORS = {
  github: "text-white",
  gitlab: "text-[#FC6D26]",
  jenkins: "text-[#D33833]",
  circleci: "text-white",
  argocd: "text-[#EF7B4D]",
  aws: "", // Color handled inside component
  bitbucket: "text-[#2684FF]",
};

/**
 * Platform/source icon (GitHub, GitLab, Jenkins, etc.)
 */
export function SourceIcon({ source, className = "", size = 16 }) {
  const Icon = SOURCE_ICONS[source];
  const colorClass = SOURCE_COLORS[source] || "text-muted-foreground";
  
  if (!Icon) {
    return (
      <span
        className={cn(
          "inline-flex items-center justify-center bg-muted text-muted-foreground font-mono text-[10px]",
          className
        )}
        style={{ width: size, height: size }}
      >
        ?
      </span>
    );
  }
  
  return <Icon className={cn(colorClass, className)} size={size} />;
}
