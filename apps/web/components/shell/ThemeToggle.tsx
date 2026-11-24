"use client";

import { Button } from "@driplytics/ui";
import { Monitor, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { type ThemeChoice, applyTheme, storedTheme } from "@/lib/theme";

const NEXT: Record<ThemeChoice, ThemeChoice> = { light: "dark", dark: "system", system: "light" };
const ICON = { light: Sun, dark: Moon, system: Monitor };

/** Light → dark → follow the system. Dark matters: control rooms are often dim. */
export function ThemeToggle() {
  const [choice, setChoice] = useState<ThemeChoice>("system");

  useEffect(() => {
    setChoice(storedTheme());
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const follow = () => {
      if (storedTheme() === "system") applyTheme("system");
    };
    mq.addEventListener("change", follow);
    return () => mq.removeEventListener("change", follow);
  }, []);

  const Icon = ICON[choice];
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={`Theme: ${choice}. Switch to ${NEXT[choice]}`}
      title={`Theme: ${choice}`}
      onClick={() => {
        const next = NEXT[choice];
        applyTheme(next);
        setChoice(next);
      }}
    >
      <Icon />
    </Button>
  );
}
