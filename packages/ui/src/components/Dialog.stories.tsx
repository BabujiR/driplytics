import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";

import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { Field, Textarea } from "./Input";

const meta = { title: "Components/Dialog", component: Dialog } satisfies Meta<typeof Dialog>;
export default meta;
type Story = StoryObj<typeof meta>;

function DismissDemo({ initiallyOpen = false }: { initiallyOpen?: boolean }) {
  const [open, setOpen] = useState(initiallyOpen);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Dismiss finding…</Button>
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title="Dismiss this finding?"
        description="FV-101 · Passing ~4 gpm while closed · $31.5k/yr"
        footer={
          <>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setOpen(false)}>
              Dismiss
            </Button>
          </>
        }
      >
        <Field label="Reason" hint="Required. Kept in the audit trail.">
          <Textarea placeholder="e.g. valve replaced on Nov 12" />
        </Field>
      </Dialog>
    </>
  );
}

export const Closed: Story = { args: { open: false, onOpenChange: () => {}, title: "" }, render: () => <DismissDemo /> };
export const Open: Story = {
  args: { open: true, onOpenChange: () => {}, title: "" },
  render: () => <DismissDemo initiallyOpen />,
};
