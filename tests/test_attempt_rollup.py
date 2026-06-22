from contestiq_core.codeforces.normalizer import normalize_submissions, rollup_user_problem_attempts


def test_rollup_user_problem_attempts_does_not_compute_solve_time():
    raw = [
        {"id": 1, "creationTimeSeconds": 10, "author": {"members": [{"handle": "h"}], "participantType": "PRACTICE"}, "programmingLanguage": "PyPy 3", "verdict": "WRONG_ANSWER", "problem": {"contestId": 1, "index": "A", "name": "A", "rating": 800, "tags": ["dp"]}},
        {"id": 2, "creationTimeSeconds": 20, "author": {"members": [{"handle": "h"}], "participantType": "PRACTICE"}, "programmingLanguage": "PyPy 3", "verdict": "OK", "problem": {"contestId": 1, "index": "A", "name": "A", "rating": 800, "tags": ["dp"]}},
    ]
    attempts = rollup_user_problem_attempts(normalize_submissions(raw))
    assert len(attempts) == 1
    assert attempts[0].attempt_count == 2
    assert attempts[0].attempts_before_ac == 1
    assert attempts[0].first_submission_time == 10
    assert not hasattr(attempts[0], "solve_time")
