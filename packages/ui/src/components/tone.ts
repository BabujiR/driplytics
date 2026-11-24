import { CircleAlert, CircleCheck, CircleDashed, Info, OctagonAlert, TriangleAlert, type LucideIcon } from "lucide-react";

/** Semantic tones with fixed meanings across the app (CLAUDE.md §12.5). */
export type Tone = "neutral" | "info" | "success" | "warning" | "critical";

export const toneClasses: Record<Tone, { soft: string; solid: string; icon: string }> = {
  neutral: { soft: "bg-neutral-soft text-neutral-fg border-neutral-border", solid: "bg-neutral", icon: "text-neutral" },
  info: { soft: "bg-info-soft text-info-fg border-info-border", solid: "bg-info", icon: "text-info" },
  success: { soft: "bg-success-soft text-success-fg border-success-border", solid: "bg-success", icon: "text-success" },
  warning: { soft: "bg-warning-soft text-warning-fg border-warning-border", solid: "bg-warning", icon: "text-warning" },
  critical: { soft: "bg-critical-soft text-critical-fg border-critical-border", solid: "bg-critical", icon: "text-critical" },
};

/** Default icon per tone, so color is never the only signal. */
export const toneIcons: Record<Tone, LucideIcon> = {
  neutral: CircleDashed,
  info: Info,
  success: CircleCheck,
  warning: TriangleAlert,
  critical: OctagonAlert,
};

export const AlertIcon = CircleAlert;
