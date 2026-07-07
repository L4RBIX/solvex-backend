-- Store full solving context snapshots for consented users.
-- Only written when consent_for_training = TRUE (enforced in application layer).

CREATE TABLE IF NOT EXISTS copilot_context_snapshots (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           TEXT         NOT NULL,   -- matches copilot_sessions.id
    user_id              UUID,
    problem_id           TEXT,
    contest_id           INTEGER,
    problem_index        TEXT,
    language             TEXT,
    source_code          TEXT,
    selected_text        TEXT,
    cursor_line          INTEGER,
    last_status          TEXT,
    last_stdout          TEXT,
    last_stderr          TEXT,
    last_compile_output  TEXT,
    last_input           TEXT,
    last_expected_output TEXT,
    last_actual_output   TEXT,
    recent_events        JSONB,
    consent_for_training BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_copilot_snaps_session   ON copilot_context_snapshots (session_id);
CREATE INDEX IF NOT EXISTS idx_copilot_snaps_created   ON copilot_context_snapshots (created_at);
CREATE INDEX IF NOT EXISTS idx_copilot_snaps_consented ON copilot_context_snapshots (consent_for_training)
    WHERE consent_for_training = TRUE;

ALTER TABLE copilot_context_snapshots ENABLE ROW LEVEL SECURITY;
