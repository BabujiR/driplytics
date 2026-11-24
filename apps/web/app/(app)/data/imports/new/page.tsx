import { PageHeader } from "@driplytics/ui";

import { UploadWizard } from "@/components/imports/UploadWizard";
import { getAppContext } from "@/lib/api/server";

export const metadata = { title: "Upload an export" };

export default async function NewImportPage() {
  const { site } = await getAppContext();
  if (!site) return <PageHeader title="Upload an export" description="Add a site first." />;
  return (
    <>
      <PageHeader
        title="Upload a historian export"
        description="CSV or Parquet from PI or IP.21, long or wide format. The file goes straight to secure storage; nothing is sent to your control system."
        breadcrumbs={[site.name, "Data", "Imports", "Upload"]}
      />
      <UploadWizard siteId={site.id} siteName={site.name} timezone={site.timezone} />
    </>
  );
}
