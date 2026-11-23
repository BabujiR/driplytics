/**
 * Generated from packages/contracts/openapi.json by scripts/generate.mjs. Do not edit by hand.
 * Regenerate after changing the API: .\tasks.ps1 contracts
 */

export interface paths {
    "/api/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tenants/current": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Current Tenant Info
         * @description The selected organization, read through row-level security as the caller's tenant.
         */
        get: operations["current_tenant_info"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/sites": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sites */
        get: operations["list_sites"];
        put?: never;
        /** Create Site */
        post: operations["create_site"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/sites/{site_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Site */
        get: operations["get_site"];
        put?: never;
        post?: never;
        /**
         * Delete Site
         * @description Deletes the site and everything under it (areas, assets, tags, mappings, imports).
         */
        delete: operations["delete_site"];
        options?: never;
        head?: never;
        /** Update Site */
        patch: operations["update_site"];
        trace?: never;
    };
    "/api/v1/sites/{site_id}/export-profiles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Export Profiles */
        get: operations["list_export_profiles"];
        put?: never;
        /** Create Export Profile */
        post: operations["create_export_profile"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/export-profiles/{profile_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Export Profile */
        patch: operations["update_export_profile"];
        trace?: never;
    };
    "/api/v1/sites/{site_id}/tag-mappings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Tag Mappings
         * @description Every known tag of the site, mapped or not (unmapped tags have role = null).
         */
        get: operations["list_tag_mappings"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/sites/{site_id}/tag-mappings/csv": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Upload Tag Mapping Csv
         * @description Upsert mappings from a tag_mapping.csv (engine format). Validated by the engine first:
         *     any invalid line rejects the whole file with every problem listed.
         */
        put: operations["upload_tag_mapping_csv"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/sites/{site_id}/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Imports */
        get: operations["list_imports"];
        put?: never;
        /** Create Import */
        post: operations["create_import"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/imports/{import_id}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Import */
        post: operations["start_import"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/imports/{import_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Import */
        get: operations["get_import"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/imports/{import_id}/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Import Report */
        get: operations["get_import_report"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/imports/{import_id}/rejected-examples.csv": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Download Rejected Examples
         * @description Up to 20 example rows per rejection reason (the full rejected-row export comes later).
         */
        get: operations["download_rejected_examples"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Audit Events
         * @description Newest first. Filter by entity, e.g. ?entity_type=site&entity_id=<uuid>.
         */
        get: operations["list_audit_events"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Live
         * @description Liveness: the process is up. No dependency checks.
         */
        get: operations["live"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Ready
         * @description Readiness: Postgres, Redis and object storage are reachable. 503 if any check fails.
         */
        get: operations["ready"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/version": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Version */
        get: operations["version"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AuditEventOut */
        AuditEventOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * At
             * Format: date-time
             */
            at: string;
            /** Action */
            action: string;
            /** Entity Type */
            entity_type: string | null;
            /** Entity Id */
            entity_id: string | null;
            /** Before */
            before: {
                [key: string]: unknown;
            } | null;
            /** After */
            after: {
                [key: string]: unknown;
            } | null;
            /** User Email */
            user_email: string | null;
        };
        /** Body_upload_tag_mapping_csv */
        Body_upload_tag_mapping_csv: {
            /** File */
            file: string;
        };
        /** CurrentTenantOut */
        CurrentTenantOut: {
            tenant: components["schemas"]["TenantOut"];
            /**
             * Role
             * @enum {string}
             */
            role: "owner" | "admin" | "engineer" | "technician" | "viewer" | "partner";
            /** Sites */
            sites: components["schemas"]["SiteSummaryOut"][];
        };
        /** DependencyCheck */
        DependencyCheck: {
            /** Ok */
            ok: boolean;
            /** Detail */
            detail: string;
        };
        /**
         * ErrorOut
         * @description Body of every 4xx/5xx raised by the API (validation errors use FastAPI's own 422 shape).
         */
        ErrorOut: {
            /** Detail */
            detail: string;
        };
        /**
         * ExportLayoutModel
         * @description Mirror of driplytics_engine.ExportLayout. A test keeps the two in sync.
         */
        ExportLayoutModel: {
            /**
             * Format
             * @default auto
             * @enum {string}
             */
            format: "auto" | "long" | "wide";
            /**
             * Timestamp Col
             * @default timestamp
             */
            timestamp_col: string;
            /**
             * Tag Col
             * @default tag
             */
            tag_col: string;
            /**
             * Value Col
             * @default value
             */
            value_col: string;
            /**
             * Quality Col
             * @default quality
             */
            quality_col: string | null;
            /** Quality Suffix */
            quality_suffix?: string | null;
            /** Tag Columns */
            tag_columns?: string[] | null;
            /** Timestamp Format */
            timestamp_format?: string | null;
            /**
             * Sep
             * @default ,
             */
            sep: string;
            /**
             * Decimal
             * @default .
             */
            decimal: string;
            /**
             * Skiprows
             * @default 0
             */
            skiprows: number;
            /**
             * Encoding
             * @default utf-8-sig
             */
            encoding: string;
            /**
             * Wide Blank Cells
             * @default reject
             * @enum {string}
             */
            wide_blank_cells: "reject" | "ignore";
        };
        /** ExportProfileCreate */
        ExportProfileCreate: {
            /** Name */
            name: string;
            /**
             * @default {
             *       "format": "auto",
             *       "timestamp_col": "timestamp",
             *       "tag_col": "tag",
             *       "value_col": "value",
             *       "quality_col": "quality",
             *       "sep": ",",
             *       "decimal": ".",
             *       "skiprows": 0,
             *       "encoding": "utf-8-sig",
             *       "wide_blank_cells": "reject"
             *     }
             */
            layout: components["schemas"]["ExportLayoutModel"];
        };
        /** ExportProfileOut */
        ExportProfileOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Site Id
             * Format: uuid
             */
            site_id: string;
            /** Name */
            name: string;
            layout: components["schemas"]["ExportLayoutModel"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ExportProfileUpdate */
        ExportProfileUpdate: {
            /** Name */
            name?: string | null;
            layout?: components["schemas"]["ExportLayoutModel"] | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** ImportCreate */
        ImportCreate: {
            /** Filename */
            filename: string;
            /** Size Bytes */
            size_bytes: number;
            /** Export Profile Id */
            export_profile_id?: string | null;
        };
        /** ImportCreatedOut */
        ImportCreatedOut: {
            import: components["schemas"]["ImportOut"];
            upload: components["schemas"]["UploadTarget"];
        };
        /** ImportDetailOut */
        ImportDetailOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Site Id
             * Format: uuid
             */
            site_id: string;
            /** Export Profile Id */
            export_profile_id: string | null;
            /**
             * Source
             * @enum {string}
             */
            source: "upload" | "connector" | "demo";
            /** Object Key */
            object_key: string;
            /** Original Filename */
            original_filename: string | null;
            /** Size Bytes */
            size_bytes: number | null;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "uploaded" | "queued" | "running" | "succeeded" | "failed" | "cancelled";
            /**
             * Progress
             * @description 0..1 while the worker runs
             */
            progress: number;
            /** Error */
            error: string | null;
            /** Created By */
            created_by: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Started At */
            started_at: string | null;
            /** Finished At */
            finished_at: string | null;
            /** @description null until the import has succeeded */
            summary: components["schemas"]["ImportSummaryOut"] | null;
        };
        /** ImportOut */
        ImportOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Site Id
             * Format: uuid
             */
            site_id: string;
            /** Export Profile Id */
            export_profile_id: string | null;
            /**
             * Source
             * @enum {string}
             */
            source: "upload" | "connector" | "demo";
            /** Object Key */
            object_key: string;
            /** Original Filename */
            original_filename: string | null;
            /** Size Bytes */
            size_bytes: number | null;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "uploaded" | "queued" | "running" | "succeeded" | "failed" | "cancelled";
            /**
             * Progress
             * @description 0..1 while the worker runs
             */
            progress: number;
            /** Error */
            error: string | null;
            /** Created By */
            created_by: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Started At */
            started_at: string | null;
            /** Finished At */
            finished_at: string | null;
        };
        /**
         * ImportReportOut
         * @description The engine's ImportReport (accepted + rejected + duplicates = total_values, always).
         */
        ImportReportOut: {
            /** Source */
            source: string;
            /** Format */
            format: string;
            /** Timezone */
            timezone: string;
            /** Total Values */
            total_values: number;
            /** Accepted */
            accepted: number;
            /** Rejected */
            rejected: number;
            /** Duplicates */
            duplicates: number;
            /** Rejected By Reason */
            rejected_by_reason: {
                [key: string]: number;
            };
            /** Accepted Uncertain */
            accepted_uncertain: number;
            /**
             * Unmapped Tags
             * @description raw tag -> number of values
             */
            unmapped_tags: {
                [key: string]: number;
            };
            /** Scoring Allowed */
            scoring_allowed: boolean;
            /** Scoring Blocked Reasons */
            scoring_blocked_reasons: string[];
            /** Dst */
            dst: {
                [key: string]: number;
            };
            /** Totalizer Events */
            totalizer_events: components["schemas"]["TotalizerEvent"][];
            /** Totalizer Gaps */
            totalizer_gaps: number;
            /** Tags */
            tags: components["schemas"]["TagSummary"][];
            /** Blank Cells Ignored */
            blank_cells_ignored: number;
            /**
             * Rejected Examples
             * @description up to 20 per reason
             */
            rejected_examples: {
                [key: string]: components["schemas"]["RejectedExample"][];
            };
            /** Elapsed S */
            elapsed_s: number;
            /** Values Per Second */
            values_per_second: number;
            /** Output Path */
            output_path: string | null;
        };
        /** ImportSummaryOut */
        ImportSummaryOut: {
            /** Total Values */
            total_values: number;
            /** Accepted */
            accepted: number;
            /** Rejected */
            rejected: number;
            /** Duplicates */
            duplicates: number;
            /** Rejected By Reason */
            rejected_by_reason: {
                [key: string]: number;
            };
            /** Scoring Allowed */
            scoring_allowed: boolean;
        };
        /** LiveOut */
        LiveOut: {
            /**
             * Status
             * @constant
             */
            status: "ok";
        };
        /** MeOut */
        MeOut: {
            user: components["schemas"]["UserOut"];
            /** Memberships */
            memberships: components["schemas"]["MembershipOut"][];
        };
        /** MembershipOut */
        MembershipOut: {
            /**
             * Tenant Id
             * Format: uuid
             */
            tenant_id: string;
            /** Name */
            name: string;
            /** Slug */
            slug: string;
            /**
             * Plan
             * @enum {string}
             */
            plan: "pilot" | "starter" | "professional" | "enterprise";
            /**
             * Role
             * @enum {string}
             */
            role: "owner" | "admin" | "engineer" | "technician" | "viewer" | "partner";
        };
        /** ReadinessOut */
        ReadinessOut: {
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "degraded";
            /** Checks */
            checks: {
                [key: string]: components["schemas"]["DependencyCheck"];
            };
        };
        /** RejectedExample */
        RejectedExample: {
            /**
             * Seq
             * @description position of the value in the file
             */
            seq: number;
            /** Raw Tag */
            raw_tag: string | null;
            /** Timestamp */
            timestamp: string | null;
            /** Value */
            value: string | null;
        };
        /** SiteCreate */
        SiteCreate: {
            /** Name */
            name: string;
            /**
             * Timezone
             * @default America/New_York
             */
            timezone: string;
            /**
             * Industry
             * @default water_wastewater
             * @enum {string}
             */
            industry: "water_wastewater" | "food_beverage" | "power" | "pulp_paper" | "other";
            /**
             * Display Units
             * @default us
             * @enum {string}
             */
            display_units: "us" | "si";
        };
        /** SiteOut */
        SiteOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Timezone */
            timezone: string;
            /**
             * Industry
             * @enum {string}
             */
            industry: "water_wastewater" | "food_beverage" | "power" | "pulp_paper" | "other";
            /**
             * Display Units
             * @enum {string}
             */
            display_units: "us" | "si";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** SiteSummaryOut */
        SiteSummaryOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Timezone */
            timezone: string;
            /**
             * Display Units
             * @enum {string}
             */
            display_units: "us" | "si";
        };
        /** SiteUpdate */
        SiteUpdate: {
            /** Name */
            name?: string | null;
            /** Timezone */
            timezone?: string | null;
            /** Industry */
            industry?: ("water_wastewater" | "food_beverage" | "power" | "pulp_paper" | "other") | null;
            /** Display Units */
            display_units?: ("us" | "si") | null;
        };
        /**
         * TagMappingOut
         * @description One known tag of a site. Every mapping field is null while the tag is unmapped.
         */
        TagMappingOut: {
            /**
             * Tag Id
             * Format: uuid
             */
            tag_id: string;
            /** Raw Tag */
            raw_tag: string;
            /** Description */
            description: string | null;
            /** Eng Units */
            eng_units: string | null;
            /** Canonical Tag */
            canonical_tag: string | null;
            /** Role */
            role: ("flow" | "pressure" | "level" | "temperature" | "pump_state" | "valve_state" | "other") | null;
            /** Source Unit */
            source_unit: string | null;
            /** Target Unit */
            target_unit: string | null;
            /** Is Totalizer */
            is_totalizer: boolean | null;
            /** Rollover Max */
            rollover_max: number | null;
            /** Max Gap S */
            max_gap_s: number | null;
            /** State True */
            state_true: string | null;
            /** State False */
            state_false: string | null;
            /** Low Flow Cutoff */
            low_flow_cutoff: number | null;
            /** Confidence */
            confidence: number | null;
            /** Source */
            source: ("manual" | "rules" | "behavior" | "llm" | "template") | null;
            /** Confirmed At */
            confirmed_at: string | null;
        };
        /** TagMappingUploadOut */
        TagMappingUploadOut: {
            /**
             * Site Id
             * Format: uuid
             */
            site_id: string;
            /** Mapped Tags */
            mapped_tags: number;
        };
        /** TagSummary */
        TagSummary: {
            /** Tag */
            tag: string;
            /** Raw Tag */
            raw_tag: string;
            /**
             * Role
             * @enum {string}
             */
            role: "flow" | "pressure" | "level" | "temperature" | "pump_state" | "valve_state" | "other";
            /** Unit */
            unit: string;
            /** Accepted Inputs */
            accepted_inputs: number;
            /** Output Rows */
            output_rows: number;
            /** First Utc */
            first_utc: string | null;
            /** Last Utc */
            last_utc: string | null;
        };
        /** TenantOut */
        TenantOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Slug */
            slug: string;
            /**
             * Plan
             * @enum {string}
             */
            plan: "pilot" | "starter" | "professional" | "enterprise";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** TotalizerEvent */
        TotalizerEvent: {
            /** Tag */
            tag: string;
            /** Raw Tag */
            raw_tag: string;
            /**
             * Event
             * @enum {string}
             */
            event: "rollover" | "reset";
            /** Timestamp Utc */
            timestamp_utc: string;
            /** From Value */
            from_value: number;
            /** To Value */
            to_value: number;
        };
        /**
         * UploadTarget
         * @description Where the browser sends the file: one HTTP request straight to object storage.
         */
        UploadTarget: {
            /** Url */
            url: string;
            /**
             * Method
             * @constant
             */
            method: "PUT";
            /** Headers */
            headers: {
                [key: string]: string;
            };
            /**
             * Expires In
             * @description seconds until the URL stops working
             */
            expires_in: number;
        };
        /** UserOut */
        UserOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Email */
            email: string;
            /** Display Name */
            display_name: string | null;
            /** Last Login At */
            last_login_at: string | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** VersionOut */
        VersionOut: {
            /** Service */
            service: string;
            /** Version */
            version: string;
            /** Env */
            env: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    me: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    current_tenant_info: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurrentTenantOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_sites: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SiteOut"][];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_site: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SiteCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SiteOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Name already in use */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_site: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SiteOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_site: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_site: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SiteUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SiteOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Name already in use */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_export_profiles: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportProfileOut"][];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_export_profile: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExportProfileCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportProfileOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Name already in use */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_export_profile: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                profile_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExportProfileUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportProfileOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_tag_mappings: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TagMappingOut"][];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_tag_mapping_csv: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_tag_mapping_csv"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TagMappingUploadOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description File larger than 5 MB */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_imports: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportOut"][];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_import: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                site_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportCreatedOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description File too large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_import: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not uploaded yet, or already started */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Uploaded file too large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Job queue unavailable; call start again */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
        };
    };
    get_import: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportDetailOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_import_report: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportReportOut"];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_rejected_examples: {
        parameters: {
            query?: never;
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description CSV file */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/csv": string;
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_audit_events: {
        parameters: {
            query?: {
                entity_type?: string | null;
                entity_id?: string | null;
                limit?: number;
            };
            header?: {
                "x-tenant-id"?: string | null;
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditEventOut"][];
                };
            };
            /** @description Missing or invalid sign-in */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Signed in, but not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Not found (other organizations' data is never visible) */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    live: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LiveOut"];
                };
            };
        };
    };
    ready: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessOut"];
                };
            };
            /** @description A dependency is down */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessOut"];
                };
            };
        };
    };
    version: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionOut"];
                };
            };
        };
    };
}
