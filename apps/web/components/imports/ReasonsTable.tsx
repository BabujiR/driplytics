"use client";

import type { ImportReport } from "@driplytics/contracts";
import { Button, TBody, TD, TH, THead, TR, Table, TableCaption, formatCount } from "@driplytics/ui";
import { ArrowDownUp, ChevronDown, ChevronRight } from "lucide-react";
import { Fragment, useState } from "react";

import { reasonText } from "@/lib/reasons";

interface Props {
  byReason: ImportReport["rejected_by_reason"];
  examples: ImportReport["rejected_examples"];
  rejected: number;
}

type SortKey = "count" | "reason";

/** Rejection reasons, sortable, each with its example rows (CLAUDE.md §12.4: import report). */
export function ReasonsTable({ byReason, examples, rejected }: Props) {
  const [sort, setSort] = useState<SortKey>("count");
  const [open, setOpen] = useState<string | null>(null);

  const rows = Object.entries(byReason)
    .filter(([, n]) => n > 0)
    .map(([code, n]) => ({ code, n, ...reasonText(code) }))
    .sort((a, b) => (sort === "count" ? b.n - a.n || a.label.localeCompare(b.label) : a.label.localeCompare(b.label)));

  const sortButton = (key: SortKey, label: string) => (
    <button
      type="button"
      onClick={() => setSort(key)}
      className="inline-flex items-center gap-1 hover:text-fg"
      aria-label={`Sort by ${label.toLowerCase()}`}
      aria-pressed={sort === key}
    >
      {label}
      <ArrowDownUp aria-hidden className="size-3" />
    </button>
  );

  return (
    <Table>
      <TableCaption>Rejected values by reason</TableCaption>
      <THead>
        <TR>
          <TH aria-sort={sort === "reason" ? "ascending" : "none"}>{sortButton("reason", "Reason")}</TH>
          <TH numeric aria-sort={sort === "count" ? "descending" : "none"}>
            {sortButton("count", "Values")}
          </TH>
          <TH numeric>Share</TH>
          <TH>
            <span className="sr-only">Examples</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {rows.map((r) => {
          const ex = examples[r.code] ?? [];
          const expanded = open === r.code;
          return (
            <Fragment key={r.code}>
              <TR>
                <TD>
                  <div className="font-medium">{r.label}</div>
                  <div className="text-xs text-fg-muted">{r.explain}</div>
                </TD>
                <TD numeric className="font-semibold">
                  {formatCount(r.n)}
                </TD>
                <TD numeric className="text-fg-muted">
                  {rejected ? `${((r.n / rejected) * 100).toFixed(0)} %` : "—"}
                </TD>
                <TD className="text-right">
                  {ex.length ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-expanded={expanded}
                      onClick={() => setOpen(expanded ? null : r.code)}
                    >
                      {expanded ? <ChevronDown /> : <ChevronRight />}
                      {ex.length} example{ex.length === 1 ? "" : "s"}
                    </Button>
                  ) : null}
                </TD>
              </TR>
              {expanded ? (
                <TR className="bg-surface-2 hover:bg-surface-2">
                  <TD colSpan={4} className="py-3">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-left text-fg-muted">
                          <th className="py-1 pr-4 font-medium">Row in file</th>
                          <th className="py-1 pr-4 font-medium">Tag</th>
                          <th className="py-1 pr-4 font-medium">Timestamp (as in file)</th>
                          <th className="py-1 font-medium">Value</th>
                        </tr>
                      </thead>
                      <tbody className="font-mono">
                        {ex.map((e) => (
                          <tr key={e.seq}>
                            <td className="py-1 pr-4 tabular-nums">{formatCount(e.seq)}</td>
                            <td className="py-1 pr-4">{e.raw_tag ?? "—"}</td>
                            <td className="py-1 pr-4">{e.timestamp ?? "—"}</td>
                            <td className="py-1">{e.value === "" ? "(empty)" : (e.value ?? "—")}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TD>
                </TR>
              ) : null}
            </Fragment>
          );
        })}
      </TBody>
    </Table>
  );
}
