import type { Meta, StoryObj } from "@storybook/react-vite";

const meta = { title: "Foundations/Tokens" } satisfies Meta;
export default meta;

const groups: Array<[string, string[]]> = [
  ["Surfaces and text", ["bg", "surface", "surface-2", "surface-3", "border", "border-strong", "fg", "fg-muted", "fg-subtle"]],
  ["Brand", ["primary", "primary-hover", "primary-fg", "primary-soft", "primary-soft-fg", "focus"]],
  ...(["critical", "warning", "success", "neutral", "info"].map((t) => [t, [t, `${t}-soft`, `${t}-fg`, `${t}-border`]]) as Array<
    [string, string[]]
  >),
];

/** Every color is a CSS variable (--dl-*). Switch Theme in the toolbar. White-label partners override these. */
export const Colors: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-6">
      {groups.map(([name, tokens]) => (
        <section key={name}>
          <h3 className="mb-2 text-sm font-semibold capitalize">{name}</h3>
          <div className="flex flex-wrap gap-3">
            {tokens.map((t) => (
              <div key={t} className="w-32">
                <div className="h-12 rounded-md border border-border" style={{ background: `var(--dl-${t})` }} />
                <code className="mt-1 block font-mono text-xs text-fg-muted">--dl-{t}</code>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  ),
};

export const Typography: StoryObj = {
  render: () => (
    <div className="flex max-w-2xl flex-col gap-3">
      <p className="text-2xl font-semibold tracking-tight">Valve FV-101 is passing about 4 gpm while closed</p>
      <p className="text-xl font-semibold">Import report</p>
      <p className="text-base">Body text: plain words over jargon. Technical terms get a tooltip.</p>
      <p className="text-sm text-fg-muted">Muted text for context and hints.</p>
      <p className="text-2xl font-semibold tabular-nums">$84,200 · 5,179 · 1,111</p>
      <p className="font-mono text-sm">FIT-101.PV · FQI-101.TOT · P-201.RUN</p>
    </div>
  ),
};
