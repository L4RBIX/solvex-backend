-- 029_practice_pack_jobs_leases.sql
-- Lease/retry/priority columns for practice_pack_jobs batch worker.
-- Also stores normalized quality_score on duel_problem_packs.

alter table practice_pack_jobs
  add column if not exists priority_score double precision;

alter table practice_pack_jobs
  add column if not exists leased_until timestamptz;

alter table practice_pack_jobs
  add column if not exists leased_by text;

alter table practice_pack_jobs
  add column if not exists next_attempt_at timestamptz;

alter table practice_pack_jobs
  add column if not exists oracle_family text;

create index if not exists idx_practice_pack_jobs_lease
  on practice_pack_jobs (status, next_attempt_at, priority_score desc nulls last);

alter table duel_problem_packs
  add column if not exists quality_score real;

alter table duel_problem_packs
  add column if not exists oracle_family text;
