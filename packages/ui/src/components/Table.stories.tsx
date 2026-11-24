import type { Meta, StoryObj } from "@storybook/react-vite";

import { Chip } from "./Chip";
import { TBody, TD, TH, THead, TR, Table, TableCaption } from "./Table";

const rows = [
  { rank: 1, asset: "FV-101", area: "Filter gallery", problem: "Passing ~4 gpm while closed", usd: "$31.5k", conf: "High", status: "New" },
  { rank: 2, asset: "P-201", area: "High-service pumps", problem: "Flow with pump off (check valve?)", usd: "$19.8k", conf: "High", status: "Verifying" },
  { rank: 3, asset: "FIT-301 vs FIT-305", area: "Distribution", problem: "Meters disagree by 6 %", usd: "$12.1k", conf: "Medium", status: "New" },
];

const meta = { title: "Components/Table", component: Table } satisfies Meta<typeof Table>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Switch Density in the toolbar to see Compact rows. */
export const Worklist: Story = {
  render: () => (
    <Table>
      <TableCaption>Findings ranked by dollars per year</TableCaption>
      <THead>
        <TR>
          <TH numeric>#</TH>
          <TH>Asset</TH>
          <TH>Problem</TH>
          <TH numeric>$/year</TH>
          <TH>Confidence</TH>
          <TH>Status</TH>
        </TR>
      </THead>
      <TBody>
        {rows.map((r) => (
          <TR key={r.rank}>
            <TD numeric>{r.rank}</TD>
            <TD>
              <div className="font-medium">{r.asset}</div>
              <div className="text-xs text-fg-muted">{r.area}</div>
            </TD>
            <TD>{r.problem}</TD>
            <TD numeric className="font-semibold">
              {r.usd}
            </TD>
            <TD>{r.conf}</TD>
            <TD>
              <Chip tone={r.status === "Verifying" ? "info" : "neutral"}>{r.status}</Chip>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  ),
};

export const RawValues: Story = {
  render: () => (
    <Table>
      <THead>
        <TR>
          <TH>timestamp</TH>
          <TH>tag</TH>
          <TH numeric>value</TH>
          <TH>quality</TH>
        </TR>
      </THead>
      <TBody>
        {[
          ["2026-11-01 00:50:00", "FIT-101.PV", "249.81", "Good"],
          ["2026-11-01 00:50:00", "FQI-101.TOT", "999000.0", "Good"],
          ["2026-11-01 00:50:00", "P-201.RUN", "RUNNING", "Good"],
        ].map((r) => (
          <TR key={r[1]}>
            <TD mono>{r[0]}</TD>
            <TD mono>{r[1]}</TD>
            <TD mono numeric>
              {r[2]}
            </TD>
            <TD>{r[3]}</TD>
          </TR>
        ))}
      </TBody>
    </Table>
  ),
};
