import type { Meta, StoryObj } from "@storybook/react-vite";

import { Stat } from "./Stat";

const meta = {
  title: "Components/Stat",
  component: Stat,
  args: { label: "Estimated loss", value: "$84.2k", unit: "/ year", hint: "across 7 open findings" },
} satisfies Meta<typeof Stat>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Headline: Story = {
  render: () => (
    <div className="flex flex-wrap gap-10 rounded-lg border border-border bg-surface p-5">
      <Stat label="Estimated loss" value="$84.2k" unit="/ year" hint="across 7 open findings" tone="critical" />
      <Stat label="Verified fixed this quarter" value="$12.4k" tone="success" />
      <Stat label="Data freshness" value="2 h ago" hint="1 import" />
    </div>
  ),
};
