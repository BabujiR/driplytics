/**
 * Driplytics design system (ADR 0008).
 * Phase 0 placeholder: design tokens, Tailwind preset and components arrive in P0-14 / P0-15.
 */

export const brand = {
  name: "Driplytics",
  tagline: "In-plant water and energy loss detection from historian data",
} as const;

/** Join class names, skipping falsy values. */
export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
