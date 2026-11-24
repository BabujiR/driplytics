import { Smartphone } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Field kit" };

export default function FieldKitPage() {
  return (
    <ComingSoon
      title="Field kit"
      icon={Smartphone}
      phase="Phase 2"
      promise="Which valve to check and how, on a phone: verify findings in the field, attach photos and clamp-on readings."
    />
  );
}
