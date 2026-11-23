-- 0001 initial schema: tenancy, users, sites/assets/tags, imports, jobs, audit (Phase 0).
-- ADR 0003: shared schema + tenant_id on every tenant-owned row + FORCED row-level security.
-- The runtime role driplytics_app is never a superuser and never has BYPASSRLS.
-- Every policy fails closed: with no app.tenant_id set, a tenant-owned table returns no rows.

-- ------------------------------------------------------------------ runtime role
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'driplytics_app') THEN
    CREATE ROLE driplytics_app NOLOGIN;  -- LOGIN + password are set by the bootstrap step
  END IF;
END
$$;

-- ------------------------------------------------------------------ request context helpers
-- The API sets these per transaction: SELECT set_config('app.tenant_id', '<uuid>', true)
CREATE FUNCTION app_current_tenant() RETURNS uuid
  LANGUAGE sql STABLE PARALLEL SAFE
  AS $$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;

CREATE FUNCTION app_current_user() RETURNS uuid
  LANGUAGE sql STABLE PARALLEL SAFE
  AS $$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$;

-- ------------------------------------------------------------------ tenancy and users
CREATE TABLE tenant (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL CHECK (length(trim(name)) > 0),
  slug        text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  plan        text NOT NULL DEFAULT 'pilot'
              CHECK (plan IN ('pilot', 'starter', 'professional', 'enterprise')),
  partner_id  uuid REFERENCES tenant (id),
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Users are global (one person can belong to several tenants); not tenant-owned, no RLS.
CREATE TABLE app_user (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email          text NOT NULL CHECK (email = lower(email) AND email LIKE '%_@_%'),
  idp_subject    text UNIQUE,              -- the OIDC 'sub' claim; NULL until first sign-in
  display_name   text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  last_login_at  timestamptz
);
CREATE UNIQUE INDEX app_user_email_key ON app_user (email);

CREATE TABLE membership (
  tenant_id   uuid NOT NULL REFERENCES tenant (id) ON DELETE CASCADE,
  user_id     uuid NOT NULL REFERENCES app_user (id) ON DELETE CASCADE,
  role        text NOT NULL
              CHECK (role IN ('owner', 'admin', 'engineer', 'technician', 'viewer', 'partner')),
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, user_id)
);
CREATE INDEX membership_user_idx ON membership (user_id);

-- ------------------------------------------------------------------ plant model
-- Composite foreign keys (child_id, tenant_id) -> parent (id, tenant_id) make it impossible
-- to attach a row to a parent that belongs to a different tenant, even with a bug in the API.
CREATE TABLE site (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      uuid NOT NULL REFERENCES tenant (id) ON DELETE CASCADE,
  name           text NOT NULL CHECK (length(trim(name)) > 0),
  timezone       text NOT NULL DEFAULT 'America/New_York',
  industry       text NOT NULL DEFAULT 'water_wastewater',
  display_units  text NOT NULL DEFAULT 'us' CHECK (display_units IN ('us', 'si')),   -- ADR 0012
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, name),
  UNIQUE (id, tenant_id)
);

CREATE TABLE area (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  uuid NOT NULL,
  site_id    uuid NOT NULL,
  name       text NOT NULL,
  UNIQUE (site_id, name),
  UNIQUE (id, tenant_id),
  FOREIGN KEY (site_id, tenant_id) REFERENCES site (id, tenant_id) ON DELETE CASCADE
);

CREATE TABLE asset (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  uuid NOT NULL,
  area_id    uuid NOT NULL,
  kind       text NOT NULL CHECK (kind IN ('valve', 'pump', 'meter', 'tank', 'cooling_tower', 'line', 'other')),
  name       text NOT NULL,
  UNIQUE (area_id, name),
  UNIQUE (id, tenant_id),
  FOREIGN KEY (area_id, tenant_id) REFERENCES area (id, tenant_id) ON DELETE CASCADE
);

CREATE TABLE tag (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL,
  site_id      uuid NOT NULL,
  raw_tag      text NOT NULL,
  description  text,
  eng_units    text,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (site_id, raw_tag),
  UNIQUE (id, tenant_id),
  FOREIGN KEY (site_id, tenant_id) REFERENCES site (id, tenant_id) ON DELETE CASCADE
);

CREATE TABLE tag_mapping (
  tag_id           uuid PRIMARY KEY,
  tenant_id        uuid NOT NULL,
  asset_id         uuid,
  canonical_tag    text NOT NULL,
  role             text NOT NULL
                   CHECK (role IN ('flow', 'pressure', 'level', 'temperature', 'pump_state', 'valve_state', 'other')),
  source_unit      text,
  target_unit      text,
  is_totalizer     boolean NOT NULL DEFAULT false,
  rollover_max     double precision,
  max_gap_s        double precision NOT NULL DEFAULT 300,
  state_true       text,
  state_false      text,
  low_flow_cutoff  double precision,
  confidence       real CHECK (confidence BETWEEN 0 AND 1),
  rationale        text,
  source           text NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'rules', 'behavior', 'llm', 'template')),
  confirmed_by     uuid REFERENCES app_user (id),
  confirmed_at     timestamptz,
  updated_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tag_id, tenant_id) REFERENCES tag (id, tenant_id) ON DELETE CASCADE,
  FOREIGN KEY (asset_id, tenant_id) REFERENCES asset (id, tenant_id),
  CHECK (role NOT IN ('pump_state', 'valve_state') OR (state_true IS NOT NULL AND state_false IS NOT NULL))
);

CREATE TABLE export_profile (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL,
  site_id     uuid NOT NULL,
  name        text NOT NULL,
  layout      jsonb NOT NULL DEFAULT '{}'::jsonb,     -- engine ExportLayout fields
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (site_id, name),
  UNIQUE (id, tenant_id),
  FOREIGN KEY (site_id, tenant_id) REFERENCES site (id, tenant_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------ imports and jobs
CREATE TABLE data_import (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          uuid NOT NULL,
  site_id            uuid NOT NULL,
  export_profile_id  uuid,
  source             text NOT NULL DEFAULT 'upload' CHECK (source IN ('upload', 'connector', 'demo')),
  object_key         text NOT NULL,                  -- raw file in object storage (immutable)
  original_filename  text,
  size_bytes         bigint CHECK (size_bytes >= 0),
  status             text NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'uploaded', 'queued', 'running', 'succeeded', 'failed', 'cancelled')),
  progress           real NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 1),
  error              text,
  created_by         uuid REFERENCES app_user (id),
  created_at         timestamptz NOT NULL DEFAULT now(),
  started_at         timestamptz,
  finished_at        timestamptz,
  UNIQUE (id, tenant_id),
  FOREIGN KEY (site_id, tenant_id) REFERENCES site (id, tenant_id) ON DELETE CASCADE,
  FOREIGN KEY (export_profile_id, tenant_id) REFERENCES export_profile (id, tenant_id)
);
CREATE INDEX data_import_site_created_idx ON data_import (site_id, created_at DESC);

CREATE TABLE import_report (
  import_id        uuid PRIMARY KEY,
  tenant_id        uuid NOT NULL,
  total_values     bigint NOT NULL CHECK (total_values >= 0),
  accepted         bigint NOT NULL CHECK (accepted >= 0),
  rejected         bigint NOT NULL CHECK (rejected >= 0),
  duplicates       bigint NOT NULL CHECK (duplicates >= 0),
  rejected_by_reason jsonb NOT NULL DEFAULT '{}'::jsonb,
  examples         jsonb NOT NULL DEFAULT '{}'::jsonb,
  report           jsonb NOT NULL,                   -- the full engine ImportReport
  scoring_allowed  boolean NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (import_id, tenant_id) REFERENCES data_import (id, tenant_id) ON DELETE CASCADE,
  -- The accounting invariant (CLAUDE.md section 4), enforced by the database itself:
  CONSTRAINT import_report_counts_balance CHECK (accepted + rejected + duplicates = total_values)
);

CREATE TABLE job (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL REFERENCES tenant (id) ON DELETE CASCADE,
  kind         text NOT NULL,
  status       text NOT NULL DEFAULT 'queued'
               CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  attempts     integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  error        text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  started_at   timestamptz,
  finished_at  timestamptz
);
CREATE INDEX job_tenant_status_idx ON job (tenant_id, status, created_at);

-- Append-only: the runtime role may INSERT and SELECT, never UPDATE or DELETE.
CREATE TABLE audit_event (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL REFERENCES tenant (id) ON DELETE CASCADE,
  user_id      uuid REFERENCES app_user (id),
  action       text NOT NULL,                        -- e.g. 'tag_mapping.update'
  entity_type  text,
  entity_id    text,
  before       jsonb,
  after        jsonb,
  at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_event_tenant_at_idx ON audit_event (tenant_id, at DESC);

-- ------------------------------------------------------------------ row-level security
-- Standard policy for every table that has a tenant_id column.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['site', 'area', 'asset', 'tag', 'tag_mapping', 'export_profile',
                           'data_import', 'import_report', 'job', 'audit_event'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY tenant_isolation ON %I USING (tenant_id = app_current_tenant()) '
      'WITH CHECK (tenant_id = app_current_tenant())', t);
  END LOOP;
END
$$;

-- tenant: visible if it is the current tenant, or the signed-in user is a member of it
-- (needed for the "which organizations can I switch to?" list before a tenant is chosen).
ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_visible ON tenant
  USING (id = app_current_tenant()
         OR EXISTS (SELECT 1 FROM membership m WHERE m.tenant_id = tenant.id AND m.user_id = app_current_user()))
  WITH CHECK (id = app_current_tenant());

-- membership: rows of the current tenant (admin screens) or the user's own rows (org switcher).
-- Writes only inside the current tenant.
ALTER TABLE membership ENABLE ROW LEVEL SECURITY;
ALTER TABLE membership FORCE ROW LEVEL SECURITY;
CREATE POLICY membership_visible ON membership
  USING (tenant_id = app_current_tenant() OR user_id = app_current_user())
  WITH CHECK (tenant_id = app_current_tenant());

-- ------------------------------------------------------------------ privileges for the runtime role
GRANT USAGE ON SCHEMA public TO driplytics_app;
GRANT SELECT, UPDATE ON tenant TO driplytics_app;                        -- creating tenants is a provisioning step
GRANT SELECT, INSERT, UPDATE ON app_user TO driplytics_app;              -- users are never hard-deleted by the app
GRANT SELECT, INSERT, UPDATE, DELETE ON membership, site, area, asset, tag, tag_mapping,
  export_profile, data_import, import_report, job TO driplytics_app;
GRANT SELECT, INSERT ON audit_event TO driplytics_app;                   -- append-only
GRANT EXECUTE ON FUNCTION app_current_tenant(), app_current_user() TO driplytics_app;
