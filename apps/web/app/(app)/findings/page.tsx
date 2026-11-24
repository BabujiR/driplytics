import { TriangleAlert } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Findings" };

export default function FindingsPage() {
  return (
    <ComingSoon
      title="Findings"
      icon={TriangleAlert}
      phase="Phase 1"
      promise="Every detected loss with its evidence chart, what was excluded and why, the confidence and the dollars per year."
    />
  );
}
