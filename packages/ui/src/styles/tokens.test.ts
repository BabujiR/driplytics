import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const css = readFileSync(new URL("./tokens.css", import.meta.url), "utf8");
const themeCss = readFileSync(new URL("./theme.css", import.meta.url), "utf8");

function block(selector: string): Record<string, string> {
  const start = css.indexOf(`${selector} {`);
  const body = css.slice(start, css.indexOf("\n}", start));
  return Object.fromEntries([...body.matchAll(/--dl-([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2]!.trim()]));
}

const light = block('[data-theme="light"]');
const dark = block('[data-theme="dark"]');
const comfortable = block('[data-density="comfortable"]');
const compact = block('[data-density="compact"]');

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi! + 0.05) / (lo! + 0.05);
}

const TONES = ["critical", "warning", "success", "neutral", "info"];
// [foreground, background, minimum ratio]: 4.5 for text (WCAG AA), 3 for icons and focus rings
const PAIRS: Array<[string, string, number]> = [
  ["fg", "bg", 4.5],
  ["fg", "surface", 4.5],
  ["fg-muted", "surface", 4.5],
  ["fg-muted", "surface-2", 4.5],
  ["fg-subtle", "surface", 4.5],
  ["fg-subtle", "bg", 4.5],
  ["primary-fg", "primary", 4.5],
  ["primary-fg", "primary-hover", 4.5],
  ["primary-soft-fg", "primary-soft", 4.5],
  ["focus", "surface", 3],
  ...TONES.flatMap((t): Array<[string, string, number]> => [
    [`${t}-fg`, `${t}-soft`, 4.5],
    [`${t}-fg`, "surface", 4.5],
    [t, "surface", 3],
  ]),
];

describe("design tokens", () => {
  it("dark theme defines every light token, and the reverse", () => {
    expect(Object.keys(dark).sort()).toEqual(Object.keys(light).sort());
  });

  it("compact density defines every comfortable token", () => {
    expect(Object.keys(compact).sort()).toEqual(Object.keys(comfortable).sort());
  });

  it("every theme color token is exposed to Tailwind", () => {
    const missing = Object.keys(light).filter(
      (k) => !k.startsWith("shadow") && !themeCss.includes(`var(--dl-${k})`),
    );
    expect(missing).toEqual([]);
  });

  for (const [name, theme] of [
    ["light", light],
    ["dark", dark],
  ] as const) {
    it.each(PAIRS)(`${name}: %s on %s meets %d:1`, (fg, bg, min) => {
      expect(contrast(theme[fg]!, theme[bg]!)).toBeGreaterThanOrEqual(min);
    });
  }
});
