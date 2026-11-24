import type { Meta, StoryObj } from "@storybook/react-vite";
import { Upload } from "lucide-react";

import { Button } from "./Button";
import { EmptyState } from "./EmptyState";

const meta = {
  title: "Components/EmptyState",
  component: EmptyState,
  args: {
    icon: Upload,
    title: "No imports yet",
    description: "Upload a PI or IP.21 export (CSV or Parquet, long or wide format) to see its import report.",
    action: <Button variant="primary">Upload an export</Button>,
  },
} satisfies Meta<typeof EmptyState>;
export default meta;

export const Default: StoryObj<typeof meta> = {};
