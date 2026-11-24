import type { Meta, StoryObj } from "@storybook/react-vite";

import { FileDrop } from "./FileDrop";
import { LedgerBar } from "./LedgerBar";
import { ProgressBar } from "./ProgressBar";
import { Steps } from "./Steps";

const meta = { title: "Components/Upload and import", component: FileDrop } satisfies Meta<typeof FileDrop>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Drop: Story = {
  args: {
    title: "Drag and drop a CSV or Parquet export here",
    hint: "PI or IP.21 exports, long or wide format, or click to browse",
    accept: ".csv,.txt,.parquet,.pq",
    onFile: () => {},
  },
};

export const CompactDrop: Story = {
  args: { title: "Tag mapping (optional): tag_mapping.csv", compact: true, onFile: () => {} },
};

export const Progress: Story = {
  args: { title: "", onFile: () => {} },
  render: () => (
    <div className="flex max-w-lg flex-col gap-4">
      <ProgressBar value={0.42} label="Uploading" />
      <ProgressBar value={1} label="Uploaded" tone="success" />
      <ProgressBar label="Waiting for the worker" />
    </div>
  ),
};

export const Ledger: Story = {
  args: { title: "", onFile: () => {} },
  render: () => (
    <LedgerBar
      total={5179}
      segments={[
        { label: "accepted", value: 5157, tone: "success" },
        { label: "rejected", value: 19, tone: "warning" },
        { label: "duplicates", value: 3, tone: "neutral" },
      ]}
    />
  ),
};

export const WizardSteps: Story = {
  args: { title: "", onFile: () => {} },
  render: () => <Steps steps={["Upload export", "Review import", "Confirm tags", "First findings"]} current={1} />,
};
