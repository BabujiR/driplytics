import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "./Button";
import { Card, CardBody, CardFooter, CardHeader } from "./Card";
import { Stat } from "./Stat";

const meta = { title: "Components/Card", component: Card } satisfies Meta<typeof Card>;
export default meta;
type Story = StoryObj<typeof meta>;

export const LossBreakdown: Story = {
  render: () => (
    <Card className="max-w-md">
      <CardHeader title="Loss breakdown" description="Water + energy + chemicals, per year" actions={<Button size="sm">Edit assumptions</Button>} />
      <CardBody className="grid grid-cols-3 gap-4">
        <Stat label="Water" value="$22.1k" />
        <Stat label="Energy" value="$7.9k" />
        <Stat label="Chemicals" value="$1.5k" />
      </CardBody>
      <CardFooter>
        <span className="text-sm text-fg-muted">$4.20/kgal · $0.11/kWh</span>
      </CardFooter>
    </Card>
  ),
};
