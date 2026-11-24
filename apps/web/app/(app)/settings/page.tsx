import { Settings } from "lucide-react";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <ComingSoon
      title="Settings"
      icon={Settings}
      phase="Phase 1"
      promise="Loss-model inputs ($/kgal, $/kWh, chemicals), check thresholds with industry defaults, users and roles, and plan usage."
    />
  );
}
