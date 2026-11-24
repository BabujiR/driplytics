import type { Meta, StoryObj } from "@storybook/react-vite";

import { Skeleton, SkeletonText } from "./Skeleton";

const meta = { title: "Components/Skeleton", component: Skeleton } satisfies Meta<typeof Skeleton>;
export default meta;

export const Loading: StoryObj<typeof meta> = {
  render: () => (
    <div className="flex max-w-xl flex-col gap-4 rounded-lg border border-border bg-surface p-5" role="status">
      <span className="sr-only">Loading the worklist…</span>
      <Skeleton className="h-6 w-1/3" />
      <SkeletonText lines={3} />
      <Skeleton className="h-32 w-full" />
    </div>
  ),
};
