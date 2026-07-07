-- Migration 006: Personal AI Coach Memory — solving events log
-- One row per meaningful user action: run, compile error, WA, Copilot question, etc.

CREATE TABLE IF NOT EXISTS solving_events (
    id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  UUID         NULL,
    anonymous_user_key       TEXT         NULL,
    codeforces_handle        TEXT         NULL,
    session_id               UUID         NULL,
    -- Problem context
    problem_id               TEXT         NULL,
    contest_id               INTEGER      NULL,
    problem_index            TEXT         NULL,
    problem_title            TEXT         NULL,
    problem_rating           INTEGER      NULL,
    problem_tags             JSONB        NOT NULL DEFAULT '[]',
    language                 TEXT         NULL,
    -- Event classification
    event_type               TEXT         NOT NULL,  -- compile_error | runtime_error | wrong_answer | accepted | tle | copilot_question | run_attempt
    error_type               TEXT         NULL,      -- undeclared_variable | syntax | overflow | index_error | edge_case | complexity | wrong_formula | type_error | unknown
    -- Excerpts (secrets redacted before insert)
    short_summary            TEXT         NULL,      -- first 200 chars of user message / error
    source_code_excerpt      TEXT         NULL,      -- first 500 chars, redacted
    compiler_output_excerpt  TEXT         NULL,      -- first 300 chars, redacted
    runtime_output_excerpt   TEXT         NULL,      -- first 300 chars, redacted
    metadata                 JSONB        NOT NULL DEFAULT '{}',  -- mode, help_level, last_status, etc.
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_se_anon_key    ON solving_events (anonymous_user_key);
CREATE INDEX IF NOT EXISTS idx_se_user_id     ON solving_events (user_id);
CREATE INDEX IF NOT EXISTS idx_se_session_id  ON solving_events (session_id);
CREATE INDEX IF NOT EXISTS idx_se_created_at  ON solving_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_se_event_type  ON solving_events (event_type);

COMMENT ON TABLE solving_events IS
  'Audit log of every significant user solving action. '
  'Used by updateUserSolvingProfile() to aggregate error patterns and weak tags. '
  'Stored regardless of consent_for_training; excluded from training dataset exports '
  'unless user consent is present on their copilot_messages.';
