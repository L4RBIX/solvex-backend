-- 019_duel_live_state.sql
-- Phase G4.1: real-time friend duel room + Arena integration.
-- Live participant state (ready / hints / wrong attempts / judging), countdown
-- start, and safe hint log. Extends 018_duels.sql — never edits it.
-- Canonical production schema; local mirror is SQLite in
-- contestiq_api/cfdata/store.py.

alter table duel_participants add column if not exists hint_count integer not null default 0;
alter table duel_participants add column if not exists wrong_attempts integer not null default 0;
alter table duel_participants add column if not exists judging_at timestamptz;
alter table duel_participants add column if not exists last_seen_at timestamptz;
alter table duel_participants add column if not exists arena_opened_at timestamptz;

alter table duel_matches add column if not exists countdown_started_at timestamptz;
alter table duel_matches add column if not exists winner_decided_at timestamptz;

-- Safe, generic hints only — never editorials or solutions. Text is stored so
-- the same hint can be re-served idempotently; no source code ever lands here.
create table if not exists duel_hints (
  hint_id uuid primary key,
  duel_id uuid not null references duel_matches (duel_id) on delete cascade,
  participant_subject text not null,
  hint_number integer not null,
  hint_text text not null,
  created_at timestamptz not null default now()
);
create index if not exists idx_duel_hints_duel on duel_hints (duel_id, participant_subject, hint_number);

alter table duel_hints enable row level security;
