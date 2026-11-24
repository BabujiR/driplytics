import { Plug } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Connectors" };

export default function ConnectorsPage() {
  return (
    <ComingSoon
      title="Connectors"
      icon={Plug}
      phase="Phase 3"
      promise="A read-only edge connector that sends new historian data every few minutes, with health and data freshness shown here."
    />
  );
}
