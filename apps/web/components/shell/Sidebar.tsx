"use client";

import { brand, cn } from "@driplytics/ui";
import { Droplet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV, isActive } from "./nav";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 rounded-md px-2 py-1 font-semibold text-fg">
      <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-fg">
        <Droplet aria-hidden className="size-4" />
      </span>
      {brand.name}
    </Link>
  );
}

export function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex flex-col gap-4">
      {NAV.map((group, gi) => (
        <div key={gi} className="flex flex-col gap-0.5">
          {group.label ? (
            <p className="px-2.5 pb-1 text-[0.6875rem] font-semibold tracking-wider text-fg-subtle uppercase">
              {group.label}
            </p>
          ) : null}
          {group.items.map(({ href, label, icon: Icon, phase }) => {
            const active = isActive(href, pathname);
            return (
              <Link
                key={href}
                href={href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex h-(--dl-control-h) items-center gap-2.5 rounded-md px-2.5 text-sm",
                  active
                    ? "bg-primary-soft font-medium text-primary-soft-fg"
                    : "text-fg-muted hover:bg-surface-3 hover:text-fg",
                )}
              >
                <Icon aria-hidden className="size-4 shrink-0" />
                <span className="flex-1 truncate">{label}</span>
                {phase ? (
                  // On the highlighted (current) item the label takes the item's color: subtle gray on the
                  // blue highlight would fall below 4.5:1 contrast.
                  <span className={cn("text-[0.6875rem]", !active && "text-fg-subtle")} title={`Arrives in ${phase}`}>
                    soon
                  </span>
                ) : null}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col gap-6 border-r border-border bg-surface-2 px-3 py-4 md:flex">
      <Logo />
      <div className="flex-1 overflow-y-auto">
        <NavLinks />
      </div>
      <p className="px-2.5 text-[0.6875rem] text-fg-subtle">{brand.tagline}</p>
    </aside>
  );
}
