"use client";

import { Button, Chip, MenuItem, MenuLabel, MenuSeparator, Popover, Select, initials } from "@driplytics/ui";
import { Building, Check, Clock, LogOut, Menu, Rows3, Rows4 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { setSelectionCookie } from "@/lib/api/browser";
import { type Density, applyDensity, storedDensity } from "@/lib/theme";

import { CommandMenu } from "./CommandMenu";
import { Logo, NavLinks } from "./Sidebar";
import { ThemeToggle } from "./ThemeToggle";

export interface ShellUser {
  email: string;
  name: string | null;
  role: string;
}

export interface ShellOrg {
  id: string;
  name: string;
}

export interface ShellSite {
  id: string;
  name: string;
  timezone: string;
}

interface TopbarProps {
  user: ShellUser;
  orgs: ShellOrg[];
  orgId: string;
  sites: ShellSite[];
  siteId: string | null;
}

export function Topbar({ user, orgs, orgId, sites, siteId }: TopbarProps) {
  const router = useRouter();
  const site = sites.find((s) => s.id === siteId) ?? null;

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-surface/95 px-3 backdrop-blur sm:px-4">
      <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu" popoverTarget="dl-mobile-nav">
        <Menu />
      </Button>
      <Popover id="dl-mobile-nav" className="top-14 left-2 max-h-[80dvh] w-64 overflow-y-auto p-3 md:hidden">
        <div className="mb-3">
          <Logo />
        </div>
        <NavLinks onNavigate={() => document.getElementById("dl-mobile-nav")?.hidePopover()} />
      </Popover>

      {sites.length > 1 ? (
        <Select
          aria-label="Site"
          className="w-auto max-w-56 font-medium"
          value={siteId ?? ""}
          onChange={(e) => {
            setSelectionCookie("dl_site", e.target.value);
            router.refresh();
          }}
        >
          {sites.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
      ) : (
        <span className="truncate px-1 text-sm font-medium text-fg">{site?.name ?? "No sites yet"}</span>
      )}

      <div className="hidden min-w-0 flex-1 justify-center lg:flex">
        <CommandMenu />
      </div>
      <div className="flex-1 lg:hidden" />

      {site ? (
        <span className="hidden items-center gap-1 text-xs text-fg-muted xl:flex" title="All times on screen use the site's time zone">
          <Clock aria-hidden className="size-3.5" />
          {site.timezone}
        </span>
      ) : null}

      <ThemeToggle />
      <UserMenu user={user} orgs={orgs} orgId={orgId} />
    </header>
  );
}

function UserMenu({ user, orgs, orgId }: { user: ShellUser; orgs: ShellOrg[]; orgId: string }) {
  const router = useRouter();
  const [density, setDensity] = useState<Density>("comfortable");
  useEffect(() => setDensity(storedDensity()), []);

  const chooseDensity = (d: Density) => {
    applyDensity(d);
    setDensity(d);
  };

  return (
    <>
      <button
        type="button"
        popoverTarget="dl-user-menu"
        aria-label={`Account: ${user.name ?? user.email}`}
        className="flex size-8 items-center justify-center rounded-full bg-primary-soft text-xs font-semibold text-primary-soft-fg hover:ring-2 hover:ring-border-strong"
      >
        {initials(user.name ?? user.email)}
      </button>
      <Popover id="dl-user-menu" className="top-14 right-2 w-72">
        <div className="px-2.5 py-2">
          <p className="truncate text-sm font-semibold">{user.name ?? user.email}</p>
          <p className="truncate text-xs text-fg-muted">{user.email}</p>
          <Chip className="mt-2 capitalize">{user.role}</Chip>
        </div>
        {orgs.length > 1 ? (
          <>
            <MenuSeparator />
            <MenuLabel>Organization</MenuLabel>
            {orgs.map((o) => (
              <MenuItem
                key={o.id}
                aria-current={o.id === orgId ? "true" : undefined}
                onClick={() => {
                  setSelectionCookie("dl_tenant", o.id);
                  setSelectionCookie("dl_site", null);
                  document.getElementById("dl-user-menu")?.hidePopover();
                  router.push("/");
                  router.refresh();
                }}
              >
                <Building />
                <span className="flex-1 truncate">{o.name}</span>
                {o.id === orgId ? <Check aria-hidden /> : null}
              </MenuItem>
            ))}
          </>
        ) : null}
        <MenuSeparator />
        <MenuLabel>Density</MenuLabel>
        <MenuItem aria-pressed={density === "comfortable"} onClick={() => chooseDensity("comfortable")}>
          <Rows3 />
          <span className="flex-1">Comfortable</span>
          {density === "comfortable" ? <Check aria-hidden /> : null}
        </MenuItem>
        <MenuItem aria-pressed={density === "compact"} onClick={() => chooseDensity("compact")}>
          <Rows4 />
          <span className="flex-1">Compact (big tables)</span>
          {density === "compact" ? <Check aria-hidden /> : null}
        </MenuItem>
        <MenuSeparator />
        <form method="post" action="/auth/logout">
          <MenuItem type="submit">
            <LogOut />
            Sign out
          </MenuItem>
        </form>
      </Popover>
    </>
  );
}
