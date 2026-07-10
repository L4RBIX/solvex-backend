"""Copilot evidence-verification pipeline (hotfix for false 'wrong solution' claims).

Root cause: the LLM was told to "mentally run" code and invent counterexamples
from its own training knowledge, with zero execution behind it. For external
Codeforces problems the catalog stores no official statement or tests, so the
model has no oracle — and it hallucinated a false negative verdict on CF
1393B "Applejack and Storages" (claimed the answer should be NO for an input
where the correct, accepted answer is YES).

These tests exercise the deterministic evidence-classification + anti-
hallucination guard, independent of any real DeepSeek network call.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api.routes.copilot import (
    EVIDENCE_COMPILE_ERROR,
    EVIDENCE_NO_VERIFIED_FAILURE,
    EVIDENCE_RUNTIME_ERROR,
    EVIDENCE_SPECULATIVE_REVIEW,
    EVIDENCE_VERIFIED_COUNTEREXAMPLE,
    EVIDENCE_VERIFIED_TEST_FAILURE,
    ExecutionContext,
    _classify_execution_evidence,
    _contains_negative_correctness_claim,
    _enforce_evidence_policy,
)

ADMIN_KEY = "copilot-evidence-admin-key"

# The exact fabricated counterexample from the production bug report: DeepSeek
# claimed the Applejack solution (quads >= 1 && pairs >= 4) was wrong on this
# input, asserting the answer "should be NO" — but the correct answer is YES
# (four sticks of length 2 form one square, four of length 1 form another).
APPLEJACK_FALSE_CLAIM = (
    "Your code is wrong. Consider this counterexample:\n\n"
    "8\n1 1 1 1 2 2 2 2\n1\n+ 1\n\n"
    "Your code outputs YES, but the expected answer is NO, because the "
    "rectangle cannot use the same length twice."
)

APPLEJACK_UNCERTAIN_REVIEW = (
    "One thing I'd double check (not yet verified): make sure the quads/pairs "
    "counting handles duplicate lengths correctly."
)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


# ─── _classify_execution_evidence: deterministic, from real execution only ───


def test_evidence_compile_error():
    ctx = ExecutionContext(last_status="compilation_error", last_compile_output="error: expected ';'")
    assert _classify_execution_evidence(ctx) == EVIDENCE_COMPILE_ERROR


def test_evidence_runtime_error():
    ctx = ExecutionContext(last_status="runtime_error")
    assert _classify_execution_evidence(ctx) == EVIDENCE_RUNTIME_ERROR


def test_evidence_verified_test_failure_requires_expected_and_actual():
    ctx = ExecutionContext(
        last_status="wrong_answer",
        last_expected_output="42",
        last_actual_output="41",
    )
    assert _classify_execution_evidence(ctx) == EVIDENCE_VERIFIED_TEST_FAILURE


def test_evidence_wrong_answer_without_actual_output_is_not_verified():
    # Status says wrong_answer but we never captured expected/actual — nothing
    # to actually point to, so this must NOT count as verified.
    ctx = ExecutionContext(last_status="wrong_answer")
    assert _classify_execution_evidence(ctx) == EVIDENCE_NO_VERIFIED_FAILURE


def test_evidence_accepted_or_idle_is_no_verified_failure():
    assert _classify_execution_evidence(ExecutionContext(last_status="accepted")) == EVIDENCE_NO_VERIFIED_FAILURE
    assert _classify_execution_evidence(ExecutionContext(last_status="Idle")) == EVIDENCE_NO_VERIFIED_FAILURE


# ─── _contains_negative_correctness_claim: narrow, doesn't flag generic hints ─


def test_negative_claim_detected_in_applejack_text():
    assert _contains_negative_correctness_claim(APPLEJACK_FALSE_CLAIM) is True


def test_generic_hint_not_flagged_as_negative_claim():
    generic = "You should check edge cases like n=0 and n=1, and make sure you're not overflowing int."
    assert _contains_negative_correctness_claim(generic) is False


def test_positive_review_not_flagged():
    positive = "This approach looks reasonable — let's trace through the sample together."
    assert _contains_negative_correctness_claim(positive) is False


def test_hedged_review_not_flagged():
    assert _contains_negative_correctness_claim(APPLEJACK_UNCERTAIN_REVIEW) is False


# ─── _enforce_evidence_policy: the actual bug fix ─────────────────────────────


def test_unverified_claim_cannot_be_presented_as_fact():
    """Task requirement #1: any negative-correctness claim without verified
    execution evidence must be downgraded and disclaimed, never presented as
    fact."""
    text, evidence, verified_wrong = _enforce_evidence_policy(
        APPLEJACK_FALSE_CLAIM, EVIDENCE_NO_VERIFIED_FAILURE
    )
    assert verified_wrong is False
    assert evidence == EVIDENCE_SPECULATIVE_REVIEW
    assert "cannot confirm this solution is wrong" in text.lower()
    assert text.index("cannot confirm") < text.index("Your code is wrong")  # disclaimer leads


def test_applejack_invalid_counterexample_is_rejected():
    """Task requirement #2 / required regression: the exact fabricated
    Applejack counterexample must never stand as a proven verdict when no
    execution actually backs it."""
    text, evidence, verified_wrong = _enforce_evidence_policy(
        APPLEJACK_FALSE_CLAIM, EVIDENCE_NO_VERIFIED_FAILURE
    )
    assert evidence != EVIDENCE_VERIFIED_COUNTEREXAMPLE
    assert verified_wrong is False
    assert text.startswith("⚠️ Unverified claim")


def test_claim_backed_by_verified_test_failure_is_trusted():
    text, evidence, verified_wrong = _enforce_evidence_policy(
        "Your code is wrong: it outputs 41 but expected 42 on the given input.",
        EVIDENCE_VERIFIED_TEST_FAILURE,
    )
    assert evidence == EVIDENCE_VERIFIED_COUNTEREXAMPLE
    assert verified_wrong is True
    assert text.startswith("Your code is wrong")  # not disclaimed — it's real


def test_claim_backed_by_compile_error_is_trusted():
    text, evidence, verified_wrong = _enforce_evidence_policy(
        "This is incorrect — it won't even compile due to a missing semicolon.",
        EVIDENCE_COMPILE_ERROR,
    )
    assert evidence == EVIDENCE_COMPILE_ERROR
    assert verified_wrong is True
    assert not text.startswith("⚠️")


def test_no_claim_no_disclaimer_needed():
    text, evidence, verified_wrong = _enforce_evidence_policy(
        "Here's a small hint: think about which quantity stays invariant.",
        EVIDENCE_NO_VERIFIED_FAILURE,
    )
    assert text == "Here's a small hint: think about which quantity stays invariant."
    assert verified_wrong is False
    assert evidence == EVIDENCE_NO_VERIFIED_FAILURE


def test_hedged_review_passes_through_unmodified():
    text, evidence, verified_wrong = _enforce_evidence_policy(
        APPLEJACK_UNCERTAIN_REVIEW, EVIDENCE_NO_VERIFIED_FAILURE
    )
    assert text == APPLEJACK_UNCERTAIN_REVIEW
    assert verified_wrong is False


# ─── End-to-end route test (DeepSeek call mocked, not the policy logic) ──────


def test_route_downgrades_hallucinated_applejack_verdict(client):
    with patch(
        "contestiq_api.routes.copilot._call_deepseek",
        new_callable=AsyncMock,
        return_value=(APPLEJACK_FALSE_CLAIM, "deepseek-chat"),
    ):
        response = client.post(
            "/api/copilot",
            json={
                "message": "Is my solution correct?",
                "mode": "approach_review",
                "help_level": 2,
                "problem": {
                    "id": "1393B",
                    "contest_id": 1393,
                    "index": "B",
                    "title": "Applejack and Storages",
                    "tags": ["data structures", "implementation"],
                    "rating": 1900,
                },
                "editor": {
                    "language": "cpp17",
                    "source_code": "int quads=0, pairs=0; /* ... */",
                },
                "execution": {"last_status": "Idle"},
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["evidence_type"] == "speculative_review"
    assert body["verified_wrong"] is False
    assert "cannot confirm this solution is wrong" in body["message"].lower()


def test_route_trusts_verified_wrong_answer(client):
    with patch(
        "contestiq_api.routes.copilot._call_deepseek",
        new_callable=AsyncMock,
        return_value=("Your code is wrong: it outputs 41 but expected 42.", "deepseek-chat"),
    ):
        response = client.post(
            "/api/copilot",
            json={
                "message": "Why is this failing?",
                "mode": "debug",
                "help_level": 3,
                "editor": {"language": "cpp17", "source_code": "int main(){}"},
                "execution": {
                    "last_status": "wrong_answer",
                    "last_expected_output": "42",
                    "last_actual_output": "41",
                },
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["evidence_type"] == "verified_counterexample"
    assert body["verified_wrong"] is True
    assert not body["message"].startswith("⚠️")
