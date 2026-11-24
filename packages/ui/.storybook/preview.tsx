import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "./preview.css";

import type { Preview } from "@storybook/react-vite";

import { ToastProvider } from "../src/components/Toast";

/** Toolbar: switch theme and density for every story (they set data-theme / data-density on <html>). */
const preview: Preview = {
  globalTypes: {
    theme: {
      description: "Color theme",
      toolbar: { title: "Theme", icon: "mirror", items: ["light", "dark"], dynamicTitle: true },
    },
    density: {
      description: "Density",
      toolbar: { title: "Density", icon: "component", items: ["comfortable", "compact"], dynamicTitle: true },
    },
  },
  initialGlobals: { theme: "light", density: "comfortable" },
  decorators: [
    (Story, context) => {
      document.documentElement.dataset.theme = String(context.globals.theme ?? "light");
      document.documentElement.dataset.density = String(context.globals.density ?? "comfortable");
      return (
        <ToastProvider>
          <div className="bg-bg p-6 text-fg">
            <Story />
          </div>
        </ToastProvider>
      );
    },
  ],
  parameters: {
    layout: "fullscreen",
    controls: { expanded: true },
    a11y: { test: "error" }, // axe checks every story (addon-a11y)
  },
};

export default preview;
