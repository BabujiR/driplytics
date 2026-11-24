import { Boxes } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Assets" };

export default function AssetsPage() {
  return (
    <ComingSoon
      title="Assets"
      icon={Boxes}
      phase="Phase 1"
      promise="Site, area and asset tree with a simple flow diagram (pump → valve → meter → tank); assets with findings are badged."
    />
  );
}
