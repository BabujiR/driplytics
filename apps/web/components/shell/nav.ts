import {
  Boxes,
  FileText,
  ListOrdered,
  type LucideIcon,
  PiggyBank,
  Plug,
  Settings,
  Smartphone,
  Tags,
  TriangleAlert,
  Upload,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Shown as "soon" until the feature ships. */
  phase?: string;
}

export interface NavGroup {
  label?: string;
  items: NavItem[];
}

/** CLAUDE.md §12.3 information architecture. */
export const NAV: NavGroup[] = [
  {
    items: [
      { href: "/", label: "Worklist", icon: ListOrdered },
      { href: "/findings", label: "Findings", icon: TriangleAlert, phase: "Phase 1" },
      { href: "/assets", label: "Assets", icon: Boxes, phase: "Phase 1" },
    ],
  },
  {
    label: "Data",
    items: [
      { href: "/data/imports", label: "Imports", icon: Upload },
      { href: "/data/tag-mapping", label: "Tag mapping", icon: Tags },
      { href: "/data/connectors", label: "Connectors", icon: Plug, phase: "Phase 3" },
    ],
  },
  {
    label: "More",
    items: [
      { href: "/field-kit", label: "Field kit", icon: Smartphone, phase: "Phase 2" },
      { href: "/savings", label: "Savings", icon: PiggyBank, phase: "Phase 2" },
      { href: "/reports", label: "Reports", icon: FileText, phase: "Phase 1" },
      { href: "/settings", label: "Settings", icon: Settings, phase: "Phase 1" },
    ],
  },
];

export function isActive(href: string, pathname: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}
