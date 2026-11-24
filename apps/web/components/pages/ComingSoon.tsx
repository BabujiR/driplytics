import { EmptyState, PageHeader } from "@driplytics/ui";
import type { LucideIcon } from "lucide-react";

interface ComingSoonProps {
  title: string;
  /** What this page will answer, in plain words. */
  promise: string;
  phase: string;
  icon: LucideIcon;
}

/** Placeholder for pages in the navigation that later phases build. */
export function ComingSoon({ title, promise, phase, icon }: ComingSoonProps) {
  return (
    <>
      <PageHeader title={title} />
      <EmptyState icon={icon} title={`${title} arrives in ${phase}`} description={promise} />
    </>
  );
}
