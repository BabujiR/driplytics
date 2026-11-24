import type { Meta, StoryObj } from "@storybook/react-vite";

import { Banner } from "./Banner";
import { Button } from "./Button";

const meta = {
  title: "Components/Banner",
  component: Banner,
  args: { title: "Import finished: every value accounted for", tone: "success" },
} satisfies Meta<typeof Banner>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Tones: Story = {
  render: () => (
    <div className="flex max-w-3xl flex-col gap-3">
      <Banner tone="info" title="Uploading from the browser comes next">
        Until then, run the demo import from the command line.
      </Banner>
      <Banner tone="success" title="Import finished: 5,179 = 5,157 accepted + 19 rejected + 3 duplicates" />
      <Banner
        tone="warning"
        title="Scoring is blocked: 1 unmapped tag"
        action={
          <Button size="sm" variant="primary">
            Map these tags
          </Button>
        }
      >
        XV-999.PV has 3 values but no role yet.
      </Banner>
      <Banner tone="neutral" title="Skipped: FV-101 has no valve position signal for this period" />
      <Banner tone="critical" title="FV-101 is passing about 4 gpm while closed: $31.5k/yr" />
    </div>
  ),
};
