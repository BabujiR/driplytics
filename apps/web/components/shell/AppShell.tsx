import type { ReactNode } from "react";

import { Sidebar } from "./Sidebar";
import { type ShellOrg, type ShellSite, type ShellUser, Topbar } from "./Topbar";

interface AppShellProps {
  user: ShellUser;
  orgs: ShellOrg[];
  orgId: string;
  sites: ShellSite[];
  siteId: string | null;
  children: ReactNode;
}

/** Sidebar + top bar around every signed-in page (CLAUDE.md §12.3). */
export function AppShell({ children, ...bar }: AppShellProps) {
  return (
    <div className="flex min-h-dvh bg-bg">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar {...bar} />
        <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
      </div>
    </div>
  );
}
