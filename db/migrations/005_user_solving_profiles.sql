-- Migration 005: Personal AI Coach Memory — user solving profiles
-- Stores each user's competitive-programming solving pattern over time.

CREATE TABLE IF NOT EXISTS user_solving_profiles (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID             NULL,            -- null for anonymous users
    anonymous_user_key   TEXT             NULL,            -- solvex_anon_user_key from localStorage
    codeforces_handle    TEXT             NULL,
    -- Preferences inferred from behaviour
    preferred_language   TEXT             NULL,            -- 'english' | 'russian' | 'kazakh' | ...
    preferred_help_style TEXT             NULL,            -- tiny_hints | conceptual | debug_guidance | detailed | solution_heavy
    -- Aggregated pattern arrays (JSONB)
    common_error_patterns JSONB           NOT NULL DEFAULT '[]', -- [{type, count}, ...]
    common_wa_patterns   JSONB            NOT NULL DEFAULT '[]', -- [string, ...]
    weak_tags            JSONB            NOT NULL DEFAULT '[]', -- [tag_string, ...]
    strong_tags          JSONB            NOT NULL DEFAULT '[]',
    repeated_mistakes    JSONB            NOT NULL DEFAULT '[]', -- [string, ...]
    coaching_notes       JSONB            NOT NULL DEFAULT '[]', -- [string, ...]
    -- Human-readable summary generated deterministically (or via AI when enabled)
    summary              TEXT             NULL,
    -- 0.0–1.0: how much data we have (more events → higher confidence)
    confidence_score     NUMERIC          NOT NULL DEFAULT 0,
    last_updated_at      TIMESTAMPTZ      NOT NULL DEFAULT now(),
    created_at           TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- Lookup index by anonymous key (most common query)
CREATE INDEX IF NOT EXISTS idx_usp_anon_key    ON user_solving_profiles (anonymous_user_key);
CREATE INDEX IF NOT EXISTS idx_usp_user_id     ON user_solving_profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_usp_cf_handle   ON user_solving_profiles (codeforces_handle);

COMMENT ON TABLE user_solving_profiles IS
  'Per-user competitive-programming coaching profile. '
  'Stores aggregated solving patterns used to personalise Copilot responses. '
  'Not exported for AI training unless consent_for_training is explicitly set on copilot_messages.';
