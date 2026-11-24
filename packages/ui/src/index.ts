/**
 * Driplytics design system (P0-14, P0-15, ADR 0008).
 * Styles: import "@driplytics/ui/styles.css" after Tailwind (see apps/web/app/globals.css).
 * Browse every component and state in Storybook: pnpm --filter @driplytics/ui storybook
 */

export const brand = {
  name: "Driplytics",
  tagline: "Every drop, accounted for.",
  description: "In-plant water and energy loss detection from historian data",
} as const;

export { cn } from "./lib/cn";
export * from "./lib/format";

export { type Tone, toneClasses, toneIcons } from "./components/tone";
export { Banner } from "./components/Banner";
export { Button, type ButtonProps, buttonVariants } from "./components/Button";
export { Card, CardBody, CardFooter, CardHeader } from "./components/Card";
export { Chip } from "./components/Chip";
export { Dialog } from "./components/Dialog";
export { EmptyState } from "./components/EmptyState";
export { FileDrop } from "./components/FileDrop";
export { Field, Input, Label, Select, Textarea } from "./components/Input";
export { Kbd } from "./components/Kbd";
export { LedgerBar, type LedgerSegment } from "./components/LedgerBar";
export { PageHeader, ReadOnlyNote } from "./components/PageHeader";
export { MenuItem, MenuLabel, MenuSeparator, Popover } from "./components/Popover";
export { ProgressBar } from "./components/ProgressBar";
export { Skeleton, SkeletonText } from "./components/Skeleton";
export { Spinner } from "./components/Spinner";
export { Stat } from "./components/Stat";
export { Steps } from "./components/Steps";
export { TBody, TD, TH, THead, TR, Table, TableCaption } from "./components/Table";
export { ToastCard, ToastProvider, type ToastOptions, useToast } from "./components/Toast";
