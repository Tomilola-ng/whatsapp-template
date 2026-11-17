from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "fileasset" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key" VARCHAR(255) NOT NULL,
    "alt_text" VARCHAR(255),
    "content_type" VARCHAR(100),
    "file_size" INT
);
COMMENT ON TABLE "fileasset" IS 'File model';
CREATE TABLE IF NOT EXISTS "accounts" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "user_type" VARCHAR(50) NOT NULL DEFAULT 'customer',
    "first_name" VARCHAR(255),
    "last_name" VARCHAR(255),
    "state" VARCHAR(255),
    "email" VARCHAR(255) UNIQUE,
    "phone_number" VARCHAR(20),
    "password" VARCHAR(255),
    "display_name_override" VARCHAR(80),
    "username" VARCHAR(32) UNIQUE,
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending_verification',
    "last_login_at" TIMESTAMPTZ,
    "auth_token_version" INT NOT NULL DEFAULT 0,
    "permissions_version" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "image_id" INT REFERENCES "fileasset" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_accounts_email_e90d21" ON "accounts" ("email");
CREATE INDEX IF NOT EXISTS "idx_accounts_user_ty_06efe1" ON "accounts" ("user_type");
CREATE INDEX IF NOT EXISTS "idx_accounts_status_973bef" ON "accounts" ("status");
CREATE INDEX IF NOT EXISTS "idx_accounts_user_ty_0d4517" ON "accounts" ("user_type", "status");
CREATE INDEX IF NOT EXISTS "idx_accounts_phone_n_fa72d4" ON "accounts" ("phone_number");
CREATE INDEX IF NOT EXISTS "idx_accounts_usernam_0adce0" ON "accounts" ("username");
COMMENT ON COLUMN "accounts"."user_type" IS 'CUSTOMER: customer\nPROVIDER: provider\nADMIN: admin';
COMMENT ON COLUMN "accounts"."status" IS 'ACTIVE: active\nSUSPENDED: suspended\nPENDING_VERIFICATION: pending_verification\nDEACTIVATED: deactivated\nBANNED: banned';
COMMENT ON TABLE "accounts" IS 'Table: accounts';
CREATE TABLE IF NOT EXISTS "account_preferences" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "push_enabled" BOOL NOT NULL DEFAULT True,
    "email_notifications_enabled" BOOL NOT NULL DEFAULT False,
    "marketing_email_enabled" BOOL NOT NULL DEFAULT False,
    "email_login_mfa_enabled" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) NOT NULL UNIQUE REFERENCES "accounts" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "account_preferences" IS 'Generic per-account notification preferences.';
CREATE TABLE IF NOT EXISTS "access_roles" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "is_system" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_access_role_slug_c6d1fe" ON "access_roles" ("slug");
COMMENT ON TABLE "access_roles" IS 'Named bundle of permissions assignable to any account.';
CREATE TABLE IF NOT EXISTS "account_access_roles" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "access_role_id" VARCHAR(50) NOT NULL REFERENCES "access_roles" ("id") ON DELETE CASCADE,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE,
    "assigned_by_id" VARCHAR(50) REFERENCES "accounts" ("id") ON DELETE SET NULL,
    CONSTRAINT "uid_account_acc_account_fc4761" UNIQUE ("account_id", "access_role_id")
);
COMMENT ON TABLE "account_access_roles" IS 'Assign an access role to an account.';
CREATE TABLE IF NOT EXISTS "permissions" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "codename" VARCHAR(100) NOT NULL UNIQUE,
    "module" VARCHAR(50) NOT NULL,
    "action" VARCHAR(50) NOT NULL,
    "description" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_permissions_module_7f0c10" ON "permissions" ("module");
CREATE INDEX IF NOT EXISTS "idx_permissions_module_d56cb3" ON "permissions" ("module", "action");
COMMENT ON TABLE "permissions" IS 'Atomic capability (e.g. accounts.edit).';
CREATE TABLE IF NOT EXISTS "access_role_permissions" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "access_role_id" VARCHAR(50) NOT NULL REFERENCES "access_roles" ("id") ON DELETE CASCADE,
    "permission_id" VARCHAR(50) NOT NULL REFERENCES "permissions" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_access_role_access__8cdcf2" UNIQUE ("access_role_id", "permission_id")
);
COMMENT ON TABLE "access_role_permissions" IS 'Join table: access role ↔ permission.';
CREATE TABLE IF NOT EXISTS "account_permissions" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "granted" BOOL NOT NULL DEFAULT True,
    "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE,
    "assigned_by_id" VARCHAR(50) REFERENCES "accounts" ("id") ON DELETE SET NULL,
    "permission_id" VARCHAR(50) NOT NULL REFERENCES "permissions" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_account_per_account_115cca" UNIQUE ("account_id", "permission_id")
);
COMMENT ON TABLE "account_permissions" IS 'Direct permission grant or deny for one account.';
CREATE TABLE IF NOT EXISTS "notifications" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "type" VARCHAR(20) NOT NULL DEFAULT 'info',
    "channel" VARCHAR(20) NOT NULL DEFAULT 'push',
    "title" VARCHAR(255) NOT NULL,
    "message" TEXT NOT NULL,
    "action_url" VARCHAR(500),
    "is_read" BOOL NOT NULL DEFAULT False,
    "sent_at" TIMESTAMPTZ,
    "read_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_notificatio_account_f2637d" ON "notifications" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_notificatio_is_read_9d9b95" ON "notifications" ("is_read");
CREATE INDEX IF NOT EXISTS "idx_notificatio_created_5f34f1" ON "notifications" ("created_at");
COMMENT ON COLUMN "notifications"."type" IS 'INFO: info\nSUCCESS: success\nWARNING: warning\nERROR: error';
COMMENT ON COLUMN "notifications"."channel" IS 'EMAIL: email\nSMS: sms\nPUSH: push';
COMMENT ON TABLE "notifications" IS 'Table: notifications';
CREATE TABLE IF NOT EXISTS "otps" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "code" VARCHAR(10),
    "code_hash" VARCHAR(64),
    "purpose" VARCHAR(50) NOT NULL DEFAULT 'account_verification',
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "attempts" INT NOT NULL DEFAULT 0,
    "max_attempts" INT NOT NULL DEFAULT 3,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "verified_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_otps_account_daeb17" ON "otps" ("account_id", "purpose", "status");
CREATE INDEX IF NOT EXISTS "idx_otps_expires_26323a" ON "otps" ("expires_at");
COMMENT ON COLUMN "otps"."purpose" IS 'ACCOUNT_VERIFICATION: account_verification\nLOGIN_VERIFICATION: login_verification\nPASSWORD_RESET: password_reset\nDELIVERY_CONFIRMATION: delivery_confirmation';
COMMENT ON COLUMN "otps"."status" IS 'PENDING: pending\nUSED: used\nEXPIRED: expired';
COMMENT ON TABLE "otps" IS 'Table: otps';
CREATE TABLE IF NOT EXISTS "password_setup_codes" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "code_hash" VARCHAR(64) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "used_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_password_se_account_443b30" ON "password_setup_codes" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_password_se_expires_bbc6f3" ON "password_setup_codes" ("expires_at");
COMMENT ON TABLE "password_setup_codes" IS 'One-time opaque code for admin password setup links.';
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "actor_type" VARCHAR(30) NOT NULL,
    "action" VARCHAR(120) NOT NULL,
    "entity_type" VARCHAR(120) NOT NULL,
    "entity_id" VARCHAR(120),
    "metadata" JSONB,
    "idempotency_key" VARCHAR(255) UNIQUE,
    "ip_address" VARCHAR(80),
    "user_agent" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "actor_account_id" VARCHAR(50) REFERENCES "accounts" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_audit_logs_entity__1b0d2b" ON "audit_logs" ("entity_type", "entity_id");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_actor_a_2edbe4" ON "audit_logs" ("actor_account_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_action_4eb755" ON "audit_logs" ("action");
COMMENT ON COLUMN "audit_logs"."actor_type" IS 'ACCOUNT: account\nSYSTEM: system\nPUBLIC: public';
COMMENT ON TABLE "audit_logs" IS 'Append-only security/business audit trail. Table: audit_logs';
CREATE TABLE IF NOT EXISTS "client_error_logs" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "message" VARCHAR(4000) NOT NULL,
    "flow" VARCHAR(120),
    "screen" VARCHAR(255),
    "email" VARCHAR(255),
    "platform" VARCHAR(40),
    "app_version" VARCHAR(80),
    "client_timestamp" TIMESTAMPTZ,
    "stack" TEXT,
    "metadata" JSONB,
    "ip_address" VARCHAR(80),
    "user_agent" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" VARCHAR(50) REFERENCES "accounts" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_client_erro_flow_ba1861" ON "client_error_logs" ("flow", "created_at");
CREATE INDEX IF NOT EXISTS "idx_client_erro_email_e95946" ON "client_error_logs" ("email");
CREATE INDEX IF NOT EXISTS "idx_client_erro_account_63d43b" ON "client_error_logs" ("account_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_client_erro_created_a609fd" ON "client_error_logs" ("created_at");
COMMENT ON TABLE "client_error_logs" IS 'Append-only client-reported errors. Table: client_error_logs';
CREATE TABLE IF NOT EXISTS "app_releases" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "platform" VARCHAR(10) NOT NULL,
    "version_name" VARCHAR(32) NOT NULL,
    "build_number" INT NOT NULL,
    "minimum_supported_version_name" VARCHAR(32) NOT NULL,
    "minimum_supported_build_number" INT NOT NULL,
    "force_update" BOOL NOT NULL DEFAULT False,
    "update_title" VARCHAR(120) NOT NULL,
    "update_message" TEXT NOT NULL,
    "store_url" VARCHAR(500) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "published_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_app_release_platfor_54a54a" UNIQUE ("platform", "build_number")
);
CREATE INDEX IF NOT EXISTS "idx_app_release_platfor_37da10" ON "app_releases" ("platform", "is_active", "published_at", "build_number");
CREATE INDEX IF NOT EXISTS "idx_app_release_publish_375992" ON "app_releases" ("published_at");
COMMENT ON COLUMN "app_releases"."platform" IS 'IOS: IOS\nANDROID: ANDROID';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "Ai2h3fAT6tqBre/q4eoJ4p//ByduO5I="
)
