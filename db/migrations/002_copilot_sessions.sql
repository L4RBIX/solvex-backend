-- Track per-problem Copilot solving sessions.
-- session_id is stored as TEXT (UUID string) for backwards compatibility
-- with existing copilot_messages rows that already use TEXT session_id.

CREATE TABLE IF NOT EXISTS copilot_sessions (
    id            TEXT         PRIMARY KEY,   -- UUID string, matches copilot_messages.session_id
    user_id       UUID,
    problem_id    TEXT,
    contest_id    INTEGER,
    problem_index TEXT,
    language      TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_copilot_sessions_problem   ON copilot_sessions (problem_id) WHERE problem_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_copilot_sessions_created   ON copilot_sessions (created_at);

ALTER TABLE copilot_sessions ENABLE ROW LEVEL SECURITY;
