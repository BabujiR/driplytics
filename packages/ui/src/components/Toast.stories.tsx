import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "./Button";
import { ToastCard, useToast } from "./Toast";

const meta = { title: "Components/Toast", component: ToastCard } satisfies Meta<typeof ToastCard>;
export default meta;
type Story = StoryObj<typeof meta>;

function Triggers() {
  const { toast } = useToast();
  return (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => toast({ title: "Tag mapping saved", description: "6 tags mapped", tone: "success" })}>
        Success
      </Button>
      <Button onClick={() => toast({ title: "Import queued", description: "historian_long.csv", tone: "info" })}>
        Info
      </Button>
      <Button onClick={() => toast({ title: "Upload link expired", description: "Start the upload again.", tone: "warning" })}>
        Warning
      </Button>
    </div>
  );
}

export const Interactive: Story = {
  args: { item: { id: 0, title: "", tone: "info", duration: 0 } },
  render: () => <Triggers />,
};

export const Appearance: Story = {
  args: { item: { id: 1, title: "Import finished", description: "5,179 values accounted for", tone: "success", duration: 0 } },
  render: (args) => (
    <div className="flex max-w-sm flex-col gap-2">
      <ToastCard {...args} />
      <ToastCard item={{ id: 2, title: "Upload link expired", description: "Start the upload again.", tone: "warning", duration: 0 }} />
    </div>
  ),
};
