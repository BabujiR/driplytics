import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(ts|tsx)"],
  addons: ["@storybook/addon-a11y"],
  framework: { name: "@storybook/react-vite", options: {} },
  async viteFinal(config) {
    const { mergeConfig } = await import("vite");
    // Automatic JSX runtime: the repo's base tsconfig says "preserve" (for Next.js), which Vite would
    // otherwise turn into React.createElement calls ("React is not defined").
    return mergeConfig(config, { plugins: [tailwindcss()], esbuild: { jsx: "automatic" } });
  },
};

export default config;
