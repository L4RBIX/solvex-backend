# ContestIQ Phase 1 Model Limitations

ContestIQ Phase 1 is a Training Intelligence backend based on public Codeforces history. It is not SkillTrace, not verification, and not a badge system.

## Data Boundary

Codeforces provides outcome/history data:

- submissions
- public verdicts
- problem tags
- problem ratings
- rating history
- attempts before accepted submissions
- solved and unsolved problem history

Codeforces alone does not provide process data. ContestIQ Phase 1 must not infer:

- exact solve time
- exact mastery
- independent solving
- authenticity
- cheating detection
- debugging rhythm
- badge readiness
- guaranteed rating improvement

## Weakness Wording

Weakness labels mean current friction evidence at a learner's observed challenge range. They are not trait statements and should not be worded as personal judgments.

Underexposure is Limited Evidence, not weakness. Sparse or low-confidence evidence is suppressed from firm public labels.

## Severity And Confidence

Severity and confidence are separate. Severity describes the strength of current friction signals. Confidence describes whether there is enough reliable evidence to surface the signal.

Public weakness labels are suppressed when effective sample size, distinct problem count, confidence, or exposure is too low.

## Calibration Scenarios

Calibration scenarios are synthetic validation cases. They help check whether the model behaves as expected under controlled evidence patterns, but they are not proof of real-world effectiveness.

## Feedback Analytics

Feedback analytics summarize collected local user feedback and outcomes. They are for manual calibration and future Recommendation Engine V2 work. They do not automatically tune the model, change thresholds, or prove recommendation effectiveness.

## Share Reports

Shareable reports are public training artifacts based on frontend-safe analysis fields. They intentionally exclude internal diagnostics, raw submissions, normalized history, feedback logs, outcomes, score components, and blocking reasons.

Share reports are not verification, not badges, and not proof of skill.
