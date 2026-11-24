import { FileText } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Reports" };

export default function ReportsPage() {
  return (
    <ComingSoon
      title="Reports"
      icon={FileText}
      phase="Phase 1"
      promise="The pilot report and a weekly summary email: what is losing money, how sure we are, and what was fixed."
    />
  );
}
