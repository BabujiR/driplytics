import type { Meta, StoryObj } from "@storybook/react-vite";

import { Chip } from "./Chip";
import { toneIcons } from "./tone";

const meta = {
  title: "Components/Chip",
  component: Chip,
  args: { children: "Verifying", tone: "info" },
  argTypes: { tone: { control: "inline-radio", options: ["neutral", "info", "success", "warning", "critical"] } },
} satisfies Meta<typeof Chip>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

/** Fixed meanings: critical = top-$ loss only, warning = attention, success = verified/saved, neutral = skipped/unknown. */
export const Tones: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Chip tone="neutral" icon={toneIcons.neutral}>
        Skipped: no valve state
      </Chip>
      <Chip tone="info" icon={toneIcons.info}>
        Verifying
      </Chip>
      <Chip tone="success" icon={toneIcons.success}>
        Savings verified
      </Chip>
      <Chip tone="warning" icon={toneIcons.warning}>
        3 unmapped tags
      </Chip>
      <Chip tone="critical" icon={toneIcons.critical}>
        $31.5k/yr loss
      </Chip>
    </div>
  ),
};
