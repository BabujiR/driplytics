import { PiggyBank } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Savings" };

export default function SavingsPage() {
  return (
    <ComingSoon
      title="Savings"
      icon={PiggyBank}
      phase="Phase 2"
      promise="Verified savings: before and after loss for every fixed finding, measured over a set window."
    />
  );
}
