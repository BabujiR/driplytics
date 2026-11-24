import { EmptyState } from "@driplytics/ui";
import { Building } from "lucide-react";
import type { ReactNode } from "react";

import { AppShell } from "@/components/shell/AppShell";
import { getAppContext } from "@/lib/api/server";

export const dynamic = "force-dynamic";

export default async function SignedInLayout({ children }: { children: ReactNode }) {
  const { me, membership, tenant, site } = await getAppContext();

  if (!membership || !tenant) {
    return (
      <main className="flex min-h-dvh items-center justify-center p-6">
        <EmptyState
          icon={Building}
          title="You're signed in, but not part of an organization yet"
          description={`Ask an administrator to invite ${me.user.email}. Then sign in again.`}
          action={
            <form method="post" action="/auth/logout">
              <button type="submit" className="text-sm font-medium text-primary underline underline-offset-4">
                Sign out
              </button>
            </form>
          }
        />
      </main>
    );
  }

  return (
    <AppShell
      user={{ email: me.user.email, name: me.user.display_name, role: membership.role }}
      orgs={me.memberships.map((m) => ({ id: m.tenant_id, name: m.name }))}
      orgId={membership.tenant_id}
      sites={tenant.sites.map((s) => ({ id: s.id, name: s.name, timezone: s.timezone }))}
      siteId={site?.id ?? null}
    >
      {children}
    </AppShell>
  );
}
