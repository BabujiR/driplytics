import type { Meta, StoryObj } from "@storybook/react-vite";

import { Field, Input, Select, Textarea } from "./Input";

const meta = { title: "Components/Input", component: Input } satisfies Meta<typeof Input>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "e.g. Riverbend WTP", "aria-label": "Site name" } };
export const Disabled: Story = { args: { value: "America/New_York", disabled: true, "aria-label": "Time zone" } };

export const Fields: Story = {
  render: () => (
    <div className="grid max-w-md gap-4">
      <Field label="Site name" hint="Shown in the site switcher and reports.">
        <Input defaultValue="Riverbend WTP" />
      </Field>
      <Field label="Time zone" error="Unknown time zone 'EST'. Use an IANA name like America/New_York.">
        <Input defaultValue="EST" />
      </Field>
      <Field label="Display units">
        <Select defaultValue="us">
          <option value="us">US (gpm, psi, °F)</option>
          <option value="si">SI (m³/h, kPa, °C)</option>
        </Select>
      </Field>
      <Field label="Reason for dismissing" hint="Required. Kept in the audit trail.">
        <Textarea placeholder="e.g. valve replaced on Nov 12" />
      </Field>
    </div>
  ),
};
