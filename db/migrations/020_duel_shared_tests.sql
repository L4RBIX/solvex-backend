-- 020_duel_shared_tests.sql
-- Hotfix: server-controlled shared test set for duel judging (Phase G4.1).
--
-- Previously each participant could submit their own independently-chosen
-- stdin/expected_output, meaning a player could pick an expected output that
-- simply matched their own program's output and always "win". This locks the
-- (stdin, expected_output) pair from the FIRST submission in a duel as the
-- canonical shared test for the whole match — every later submission, by
-- either participant, is judged against that SAME locked test. Extends
-- 018/019 — never edits them.

alter table duel_matches add column if not exists test_input text;
alter table duel_matches add column if not exists test_expected_output text;
alter table duel_matches add column if not exists test_locked_by text;
alter table duel_matches add column if not exists test_locked_at timestamptz;
