import type { Meta, StoryObj } from "@storybook/react-vite";
import { Download, Upload } from "lucide-react";

import { Button } from "./Button";

const meta = {
  title: "Components/Button",
  component: Button,
  args: { children: "Start import" },
  argTypes: {
    variant: { control: "inline-radio", options: ["primary", "secondary", "ghost", "danger"] },
    size: { control: "inline-radio", options: ["sm", "md", "lg"] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = { args: { variant: "primary" } };
export const Secondary: Story = { args: { variant: "secondary", children: "Use demo data" } };
export const Ghost: Story = { args: { variant: "ghost", children: "Cancel" } };
export const Danger: Story = { args: { variant: "danger", children: "Delete site" } };
export const Loading: Story = { args: { variant: "primary", loading: true, children: "Importing…" } };
export const Disabled: Story = { args: { variant: "primary", disabled: true } };

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      {(["sm", "md", "lg"] as const).map((size) => (
        <div key={size} className="flex flex-wrap items-center gap-2">
          <Button size={size} variant="primary">
            <Upload /> Upload export
          </Button>
          <Button size={size}>
            <Download /> Rejected rows (CSV)
          </Button>
          <Button size={size} variant="ghost">
            Cancel
          </Button>
          <Button size={size} variant="danger">
            Dismiss finding
          </Button>
        </div>
      ))}
    </div>
  ),
};
