-- Upgrade copilot_messages to support mode, help_level, and user_id.
-- The existing table schema (001_copilot_messages.sql) remains intact;
-- these columns are additive and nullable so no existing rows are affected.

ALTER TABLE copilot_messages
    ADD COLUMN IF NOT EXISTS user_id    UUID,
    ADD COLUMN IF NOT EXISTS mode       TEXT,
    ADD COLUMN IF NOT EXISTS help_level INTEGER;

-- Allow 'system' as a valid role (spec adds it alongside user/assistant)
ALTER TABLE copilot_messages
    DROP CONSTRAINT IF EXISTS copilot_messages_role_check;

ALTER TABLE copilot_messages
    ADD CONSTRAINT copilot_messages_role_check
    CHECK (role IN ('user', 'assistant', 'system'));

CREATE INDEX IF NOT EXISTS idx_copilot_messages_mode ON copilot_messages (mode) WHERE mode IS NOT NULL;
