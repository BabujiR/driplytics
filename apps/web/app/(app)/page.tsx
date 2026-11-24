import { Card, CardBody, CardHeader, Chip, EmptyState, PageHeader, Stat, formatRelative } from "@driplytics/ui";
import { Building, CircleCheck, Circle, ListOrdered } from "lucide-react";
import Link from "next/link";

import { getAppContext, load } from "@/lib/api/server";
import { importStatus } from "@/lib/imports";

export const metadata = { title: "Worklist" };

export default async function WorklistPage() {
  const { site, api } = await getAppContext();
  if (!site || !api) {
    return (
      <EmptyState
        icon={Building}
        title="No sites yet"
        description="An administrator adds the first site (plant) for this organization; then you can upload historian data."
      />
    );
  }

  const params = { params: { path: { site_id: site.id } } };
  const [imports, tags] = await Promise.all([
    load(api.GET("/api/v1/sites/{site_id}/imports", params)),
    load(api.GET("/api/v1/sites/{site_id}/tag-mappings", params)),
  ]);
  const latest = imports[0];
  const mapped = tags.filter((t) => t.role !== null).length;
  const steps = [
    { done: imports.length > 0, label: "Upload a historian export", href: "/data/imports" },
    { done: imports.some((i) => i.status === "succeeded"), label: "Review the import report", href: "/data/imports" },
    { done: tags.length > 0 && mapped === tags.length, label: "Confirm the tag mapping", href: "/data/tag-mapping" },
    { done: false, label: "See the first findings (Phase 1)", href: "/findings" },
  ];

  return (
    <>
      <PageHeader
        title="Worklist"
        description="What's losing money at this site, ranked by dollars per year, with what to do next."
        breadcrumbs={[site.name, "Worklist"]}
      />

      <Card className="mb-(--dl-gap)">
        <CardBody className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <Stat label="Estimated loss" value="—" hint="Findings arrive in Phase 1" />
          <Stat
            label="Latest import"
            value={latest ? formatRelative(latest.created_at) : "None yet"}
            hint={latest ? `${latest.original_filename ?? "file"} · ${importStatus(latest).label}` : "Upload an export to start"}
          />
          <Stat
            label="Tags mapped"
            value={`${mapped} of ${tags.length}`}
            hint={tags.length && mapped < tags.length ? "Scoring waits for every tag" : "Ready for scoring"}
          />
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-(--dl-gap) lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Get started" description="From upload to a dollar-ranked finding." />
          <CardBody>
            <ol className="flex flex-col gap-1">
              {steps.map((s, i) => (
                <li key={s.label}>
                  <Link
                    href={s.href}
                    className="flex items-center gap-3 rounded-md px-2 py-2 text-sm hover:bg-surface-2"
                  >
                    {s.done ? (
                      <CircleCheck aria-hidden className="size-5 text-success" />
                    ) : (
                      <Circle aria-hidden className="size-5 text-fg-subtle" />
                    )}
                    <span className={s.done ? "text-fg-muted line-through" : "text-fg"}>
                      {i + 1}. {s.label}
                    </span>
                    <span className="sr-only">{s.done ? "(done)" : "(to do)"}</span>
                  </Link>
                </li>
              ))}
            </ol>
          </CardBody>
        </Card>

        <div className="lg:col-span-2">
          <EmptyState
            icon={ListOrdered}
            title="No findings yet"
            description="Once leak-by and pump checks run (Phase 1), each finding appears here with its dollars per year, confidence and the next step."
            action={<Chip tone="info">Phase 1</Chip>}
          />
        </div>
      </div>
    </>
  );
}
