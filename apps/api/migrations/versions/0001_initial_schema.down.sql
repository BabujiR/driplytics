-- Reverse of 0001. Drops everything 0001 created except the driplytics_app role
-- (roles are cluster-wide and may be shared by other databases, e.g. tests).
DROP TABLE IF EXISTS audit_event, job, import_report, data_import, export_profile, tag_mapping,
  tag, asset, area, site, membership, app_user, tenant CASCADE;
DROP FUNCTION IF EXISTS app_current_tenant();
DROP FUNCTION IF EXISTS app_current_user();
