import type { Meta, StoryObj } from "@storybook/react-vite";
import { LogOut, Rows3 } from "lucide-react";

import { Button } from "./Button";
import { MenuItem, MenuLabel, MenuSeparator, Popover } from "./Popover";

const meta = { title: "Components/Popover menu", component: Popover } satisfies Meta<typeof Popover>;
export default meta;

export const UserMenu: StoryObj<typeof meta> = {
  args: { id: "story-menu", children: null },
  render: () => (
    <>
      <Button popoverTarget="story-menu">Open menu</Button>
      <Popover id="story-menu" className="top-20 left-6 w-64">
        <MenuLabel>Density</MenuLabel>
        <MenuItem>
          <Rows3 /> Comfortable
        </MenuItem>
        <MenuSeparator />
        <MenuItem>
          <LogOut /> Sign out
        </MenuItem>
      </Popover>
    </>
  ),
};
