# 0008. Design system: Tailwind, shadcn/ui and design tokens

- **Status:** Accepted
- **Date:** 2026-11-22

## Decision
Tailwind CSS + shadcn/ui (Radix primitives) + Lucide icons. All colors, type, spacing, radii and shadows are **design tokens** (CSS variables) in `packages/ui`, with light and dark themes and Comfortable/Compact density. Pages may only use `packages/ui` components. Storybook documents every component and state. Inter for UI with tabular numerals; JetBrains Mono for tag names. A placeholder water-blue brand until a real logo exists (ADR 0016).

## Consequences
A consistent, accessible UI, white-labeling by overriding tokens, and visual regression testing on Storybook stories.
