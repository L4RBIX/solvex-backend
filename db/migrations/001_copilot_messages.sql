-- Copilot conversation storage for SolveX AI Copilot
-- Run once in your Supabase SQL editor (or psql).

CREATE TABLE IF NOT EXISTS copilot_messages (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           TEXT         NOT NULL,
    problem_id           TEXT,
    language             TEXT         NOT NULL,
    role                 TEXT         NOT NULL CHECK (role IN ('user', 'assistant')),
    content              TEXT         NOT NULL,
    code_snapshot        TEXT,
    error_snapshot       TEXT,
    model                TEXT,
    consent_for_training BOOLEAN      NOT NULL DEFAULT FALSE,
    metadata             JSONB        NOT NULL DEFAULT '{}',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_copilot_messages_session_id  ON copilot_messages (session_id);
CREATE INDEX IF NOT EXISTS idx_copilot_messages_created_at  ON copilot_messages (created_at);
CREATE INDEX IF NOT EXISTS idx_copilot_messages_problem_id  ON copilot_messages (problem_id) WHERE problem_id IS NOT NULL;

-- Row-level security: service role bypasses; anon/authenticated roles have no access.
ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;
