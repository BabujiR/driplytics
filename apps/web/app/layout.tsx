import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";

import { ToastProvider, brand } from "@driplytics/ui";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { themeInitScript } from "@/lib/theme";

export const metadata: Metadata = {
  title: { default: brand.name, template: `%s · ${brand.name}` },
  description: brand.description,
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f7fa" },
    { media: "(prefers-color-scheme: dark)", color: "#0c131b" },
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // data-theme / data-density are set by the inline script before paint; React must not undo them.
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
