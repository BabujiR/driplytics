import { isReady, type ReadinessResponse } from "@driplytics/contracts";
import { Banner, Card, CardHeader, Chip, PageHeader, TBody, TD, TH, THead, TR, Table, brand } from "@driplytics/ui";

import Link from "next/link";

import { apiInternalUrl } from "@/lib/auth/config";

// Public (no sign-in): shows whether the local stack is healthy. Always rendered on request.
export const dynamic = "force-dynamic";
export const metadata = { title: "Stack status" };

async function getReadiness(): Promise<ReadinessResponse | null> {
  try {
    const res = await fetch(`${apiInternalUrl()}/health/ready`, { cache: "no-store" });
    return (await res.json()) as ReadinessResponse;
  } catch {
    return null;
  }
}

export default async function StatusPage() {
  const readiness = await getReadiness();
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <PageHeader title={`${brand.name} stack status`} description={brand.tagline} />
      {readiness === null ? (
        <Banner tone="warning" title="API not reachable">
          Is the api container running? Try <code className="font-mono">docker compose ps</code>.
        </Banner>
      ) : (
        <Card>
          <CardHeader
            title="Dependencies"
            actions={
              <Chip tone={isReady(readiness) ? "success" : "warning"}>
                {isReady(readiness) ? "API ready" : "API degraded"}
              </Chip>
            }
          />
          <div className="p-(--dl-card-p)">
            <Table>
              <THead>
                <TR>
                  <TH>Dependency</TH>
                  <TH>Status</TH>
                  <TH>Detail</TH>
                </TR>
              </THead>
              <TBody>
                {Object.entries(readiness.checks).map(([name, check]) => (
                  <TR key={name}>
                    <TD>{name}</TD>
                    <TD>
                      <Chip tone={check.ok ? "success" : "warning"}>{check.ok ? "OK" : "Down"}</Chip>
                    </TD>
                    <TD className="text-fg-muted">{check.detail}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </div>
        </Card>
      )}
      <p className="mt-6 text-sm text-fg-muted">
        <Link className="text-primary underline underline-offset-4" href="/">
          Open the app
        </Link>{" "}
        ·{" "}
        <a className="text-primary underline underline-offset-4" href="https://storage.googleapis.com/driplytics-demo/index.html">
          Wireframes
        </a>{" "}
        ·{" "}
        <a className="text-primary underline underline-offset-4" href="http://localhost:8000/api/docs">
          API docs
        </a>
      </p>
    </main>
  );
}
