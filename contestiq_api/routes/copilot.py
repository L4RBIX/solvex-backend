"""POST /api/copilot — Context-aware AI Copilot powered by DeepSeek (server-side only)."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections import defaultdict
from threading import Lock
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from contestiq_api import auth
from contestiq_api.coach_service import (
    detect_error_type as _coach_detect_error_type,
    format_profile_for_prompt,
    load_profile,
    save_solving_event,
)
from contestiq_api.errors import APIError
from contestiq_api.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# ─── Rate limiting (in-memory, per IP) ───────────────────────────────────────
# Sliding windows: 20 req/min and 100 req/hour per IP
_RATE_WINDOW_MIN = 60
_RATE_WINDOW_HOUR = 3600
_RATE_MAX_MIN = 20
_RATE_MAX_HOUR = 100

_rate_min: dict[str, list[float]] = defaultdict(list)
_rate_hour: dict[str, list[float]] = defaultdict(list)
_rate_lock = Lock()


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    with _rate_lock:
        cutoff_min = now - _RATE_WINDOW_MIN
        _rate_min[client_ip] = [t for t in _rate_min[client_ip] if t > cutoff_min]
        if len(_rate_min[client_ip]) >= _RATE_MAX_MIN:
            raise APIError(
                "copilot_rate_limited",
                "Too many Copilot requests. Please wait a moment before trying again.",
                status_code=429,
            )
        cutoff_hour = now - _RATE_WINDOW_HOUR
        _rate_hour[client_ip] = [t for t in _rate_hour[client_ip] if t > cutoff_hour]
        if len(_rate_hour[client_ip]) >= _RATE_MAX_HOUR:
            raise APIError(
                "copilot_rate_limited",
                "Hourly Copilot limit reached. Please try again later.",
                status_code=429,
            )
        _rate_min[client_ip].append(now)
        _rate_hour[client_ip].append(now)


# ─── Secret redaction ─────────────────────────────────────────────────────────
_SECRET_PATTERNS = [
    re.compile(r"sk[-_][A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(?:api[_-]?key|apikey)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(?:password|passwd|pwd)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(?:secret|token|auth[_-]?key|bearer)\s*[=:]\s*\S+"),
    re.compile(r"(?i)SUPABASE_SERVICE_KEY\s*[=:]\s*\S+"),
    re.compile(r"eyJ[A-Za-z0-9+/=]{20,}"),   # JWT-shaped strings
]


def _redact_secrets(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


# ─── Input size limits ────────────────────────────────────────────────────────
_MAX_MESSAGE_BYTES = 4 * 1024      # 4 KB
_MAX_CODE_BYTES    = 100 * 1024    # 100 KB
_MAX_STMT_CHARS    = 3000          # trim oversized problem statements
_MAX_ERROR_CHARS   = 2000


# ─── Request models ───────────────────────────────────────────────────────────

CopilotMode = Literal["hint", "debug", "error_explain", "approach_review", "optimize", "general"]


class ProblemContext(BaseModel):
    id: str | None = None
    contest_id: int | None = None
    index: str | None = None
    title: str | None = None
    statement: str | None = None
    input: str | None = None
    output: str | None = None
    examples: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    rating: int | None = None


class EditorContext(BaseModel):
    language: str = "cpp17"
    source_code: str = ""
    cursor_line: int | None = None
    selected_text: str | None = None

    @field_validator("source_code")
    @classmethod
    def _trim_code(cls, v: str) -> str:
        if len(v.encode()) > _MAX_CODE_BYTES:
            half = _MAX_CODE_BYTES // 2
            return v[:half] + "\n... (middle truncated for context) ...\n" + v[-half:]
        return v


class ExecutionContext(BaseModel):
    last_status: str = "Idle"
    last_stdout: str = ""
    last_stderr: str = ""
    last_compile_output: str = ""
    last_input: str = ""
    last_expected_output: str = ""
    last_actual_output: str = ""


class RecentEvent(BaseModel):
    type: str
    timestamp: str | None = None
    summary: str | None = None
    metadata: dict = Field(default_factory=dict)


class CopilotRequest(BaseModel):
    session_id: str | None = None
    message: str
    mode: CopilotMode = "general"
    help_level: int = Field(default=2, ge=1, le=5)
    consent_for_training: bool = False
    anonymous_user_key: str | None = None
    # Nested context (new format)
    problem: ProblemContext | None = None
    editor: EditorContext | None = None
    execution: ExecutionContext | None = None
    recent_events: list[RecentEvent] = Field(default_factory=list)
    # Legacy flat fields (backwards compatibility)
    language: str | None = None
    source_code: str | None = None
    stdin: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    compile_output: str | None = None
    problem_key: str | None = None
    problem_name: str | None = None
    problem_statement: str | None = None

    @field_validator("message")
    @classmethod
    def _check_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v.encode()) > _MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds 4 KB limit")
        return v

    def effective_editor(self) -> EditorContext:
        if self.editor:
            return self.editor
        return EditorContext(
            language=self.language or "cpp17",
            source_code=self.source_code or "",
        )

    def effective_execution(self) -> ExecutionContext:
        if self.execution:
            return self.execution
        return ExecutionContext(
            last_status="Idle",
            last_stdout=self.stdout or "",
            last_stderr=self.stderr or "",
            last_compile_output=self.compile_output or "",
        )

    def effective_problem(self) -> ProblemContext | None:
        if self.problem:
            return self.problem
        if self.problem_key or self.problem_name or self.problem_statement:
            return ProblemContext(
                id=self.problem_key,
                title=self.problem_name,
                statement=self.problem_statement,
            )
        return None


class CopilotResponse(BaseModel):
    status: str = "ok"
    message: str
    session_id: str
    model: str
    suggested_next_action: str | None = None
    detected_issue_type: str | None = None
    # Evidence classification (see EVIDENCE VERIFICATION below): tells the
    # frontend whether a correctness claim in `message` is backed by an actual
    # execution result, or is unverified model reasoning.
    evidence_type: str = "no_verified_failure"
    verified_wrong: bool = False


# ─── Evidence verification (correctness-claim guard) ─────────────────────────
#
# Root cause of the false "your solution is wrong" bug: the LLM was instructed
# to "mentally run" the code and invent counterexamples from its own training
# knowledge of a problem — with zero execution behind it. For external
# Codeforces problems the catalog stores no official statement or tests, so
# there is no oracle to actually verify an invented counterexample against.
#
# Fix: classify the ONLY evidence we can trust — the real ExecutionContext
# (compiler/runtime/judge output already produced by Judge0) — independently
# of what the LLM says, then downgrade+disclaim any LLM claim that the code
# is wrong when that claim isn't backed by this verified evidence.

EVIDENCE_COMPILE_ERROR = "compile_error"
EVIDENCE_RUNTIME_ERROR = "runtime_error"
EVIDENCE_VERIFIED_TEST_FAILURE = "verified_test_failure"
EVIDENCE_VERIFIED_COUNTEREXAMPLE = "verified_counterexample"
EVIDENCE_SPECULATIVE_REVIEW = "speculative_review"
EVIDENCE_NO_VERIFIED_FAILURE = "no_verified_failure"

_UNVERIFIABLE_DISCLAIMER = "I cannot confirm this solution is wrong from the available tests."

# Correctness-verdict claims only — deliberately narrower than generic advice
# ("you should check edge cases") so ordinary hints aren't flagged.
_NEGATIVE_CLAIM_PATTERNS = [
    re.compile(r"\byour\s+(code|solution|program|approach|logic)\s+(is|looks?|seems?|appears?)\s+(wrong|incorrect|broken|buggy|flawed)\b", re.I),
    re.compile(r"\bthis\s+(is|looks?|seems?)\s+(wrong|incorrect)\b", re.I),
    re.compile(r"\bis\s+(definitely|clearly)?\s*incorrect\b", re.I),
    re.compile(r"\bnot\s+correct\b", re.I),
    re.compile(r"\bcounterexample\b", re.I),
    re.compile(r"\b(will|would)\s+(fail|break)\b", re.I),
    re.compile(r"\bfails?\s+(on|for|when|with)\s+(input|n\s*=|the\s+case)", re.I),
    re.compile(r"\b(the\s+)?(correct|expected|right)\s+answer\s+(should\s+be|is)\s+\S", re.I),
    re.compile(r"\byour\s+code\s+outputs?\b.{0,80}\bbut\b.{0,80}\bexpected\b", re.I),
    re.compile(r"\bshould\s+(output|print|return|be)\s+(YES|NO|\d|true|false|\"|')", re.I),
    re.compile(r"\bgives?\s+(the\s+)?wrong\s+answer\b", re.I),
]


def _contains_negative_correctness_claim(text: str) -> bool:
    return any(p.search(text) for p in _NEGATIVE_CLAIM_PATTERNS)


def _classify_execution_evidence(exec_ctx: ExecutionContext) -> str:
    """Deterministic evidence classification from REAL execution output only —
    never from LLM text. This is the trusted oracle we actually have."""
    status = (exec_ctx.last_status or "").lower().replace(" ", "_")
    if "compil" in status or exec_ctx.last_compile_output.strip():
        return EVIDENCE_COMPILE_ERROR
    if "runtime" in status:
        return EVIDENCE_RUNTIME_ERROR
    if (
        ("wrong_answer" in status or "wrong answer" in status)
        and exec_ctx.last_expected_output.strip()
        and exec_ctx.last_actual_output.strip()
    ):
        return EVIDENCE_VERIFIED_TEST_FAILURE
    return EVIDENCE_NO_VERIFIED_FAILURE


def _enforce_evidence_policy(response_text: str, evidence: str) -> tuple[str, str, bool]:
    """Copilot may call code incorrect only for verified execution failures.

    Any correctness-verdict claim not backed by `evidence` is downgraded to
    speculative_review and prefixed with the mandatory disclaimer — this is
    the actual bug fix: it makes hallucinated counterexamples (like the
    fabricated Applejack "should be NO" claim) impossible to present as fact,
    regardless of what the model generated.
    """
    claims_wrong = _contains_negative_correctness_claim(response_text)
    if not claims_wrong:
        return response_text, evidence, False

    if evidence in (EVIDENCE_COMPILE_ERROR, EVIDENCE_RUNTIME_ERROR):
        return response_text, evidence, True
    if evidence == EVIDENCE_VERIFIED_TEST_FAILURE:
        return response_text, EVIDENCE_VERIFIED_COUNTEREXAMPLE, True

    # No verified failure exists — the claim is speculative model reasoning,
    # not proof. Never let it stand alone as a verdict.
    disclaimer = (
        f"⚠️ Unverified claim — {_UNVERIFIABLE_DISCLAIMER} "
        "The note below is a code-review opinion, not a proven failure.\n\n"
    )
    return disclaimer + response_text, EVIDENCE_SPECULATIVE_REVIEW, False


# ─── System prompt ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are SolveX Copilot, a context-aware AI coach for competitive programming practice. "
    "You can see the user's current problem, sample tests, code, language, run results, and errors. "
    "You may also receive a [User Solving Profile] — a summary of this user's past mistakes, weak topics, "
    "and learning preferences built from their solving history. "
    "Use it to personalise coaching: adapt your language, hint depth, and debugging examples, "
    "and gently remind the user of recurring mistakes without shaming them. "
    "If no profile is present, proceed normally.\n\n"

    "LEARNING-FIRST RULES:\n"
    "- Your goal is to help the user learn and debug, NOT to hand them the answer.\n"
    "- help_level 1: exactly ONE small hint, nothing more.\n"
    "- help_level 2: explain the idea without writing code.\n"
    "- help_level 3: identify the likely bug and what line/variable to inspect.\n"
    "- help_level 4: detailed explanation and pseudocode if useful.\n"
    "- help_level 5: full solution only after warning it may reduce learning value.\n\n"

    "COACHING WITH PROFILE:\n"
    "- If the profile mentions a repeated mistake (e.g. undeclared variables), check the current code "
    "for that mistake first and gently note it before answering anything else.\n"
    "- If the profile lists weak tags that match the current problem, give an extra hint in that area.\n"
    "- If the profile says the user prefers Russian or Kazakh, respond in that language.\n"
    "- If the profile says style is 'tiny_hints', keep your reply to one or two sentences maximum.\n"
    "- If the profile says the user often misses edge cases, proactively suggest testing n=0, n=1, n=2.\n\n"

    "CORRECTNESS VERIFICATION — CRITICAL:\n"
    "- You will be given a line '[Verified execution evidence: <type>]'. This reflects code that was "
    "ACTUALLY COMPILED AND RUN by the judge — it is the only ground truth you have. You did not run the "
    "code yourself, and for many problems you were not given the official statement or official tests, "
    "so your own recollection of the problem or 'mental execution' of the code CANNOT be trusted as proof.\n"
    "- You may state the code is wrong, buggy, or will fail ONLY when evidence is compile_error, "
    "runtime_error, or verified_test_failure. In that case, quote the ACTUAL input/expected/actual output "
    "already provided to you — never invent a new input.\n"
    "- If evidence is no_verified_failure (nothing has been verified to fail), do NOT claim the solution "
    "is wrong, do NOT invent a counterexample input/output, and do NOT assert what the 'correct' answer "
    "for some input should be. You may still share a code-review concern, but you MUST phrase it as a "
    "hypothesis you have not verified, e.g. 'One thing I'd double check (not yet verified): ...' — and if "
    "asked directly whether the code is correct, say: "
    f"'{_UNVERIFIABLE_DISCLAIMER}'\n"
    "- NEVER say 'your solution looks correct', 'this should work', or 'the logic is right' either, "
    "without verified evidence — when unverified, say you cannot confirm correctness either way.\n\n"

    "Use the same language as the user when possible: English, Russian, or Kazakh."
)

_MODE_INSTRUCTIONS: dict[str, str] = {
    "hint": "Give ONE small, targeted hint. Do not reveal the full approach or algorithm. 2-3 sentences max.",
    "debug": "Identify the most likely bug. Point to specific line numbers or variable names. Do NOT rewrite the full code.",
    "error_explain": "Explain what this compiler/runtime error means and its most common cause. 2-4 sentences max.",
    "approach_review": "Evaluate whether the user's overall approach is correct. Identify logical flaws without giving the full solution.",
    "optimize": "Identify the most significant performance bottleneck. Suggest the optimization direction without writing the full optimized code.",
    "general": "Answer the user's question helpfully, using hints and guidance rather than full solutions.",
}


def _build_context_message(req: CopilotRequest) -> str:
    parts: list[str] = []

    mode_instr = _MODE_INSTRUCTIONS.get(req.mode, _MODE_INSTRUCTIONS["general"])
    parts.append(
        f"[Mode: {req.mode}] [Help Level: {req.help_level}/5]\n"
        f"Instruction: {mode_instr}"
    )

    prob = req.effective_problem()
    if prob:
        header_lines: list[str] = []
        if prob.title:
            key = ""
            if prob.contest_id and prob.index:
                key = f"{prob.contest_id}{prob.index} — "
            elif prob.id:
                key = f"{prob.id} — "
            header_lines.append(f"Problem: {key}{prob.title}")
        if prob.rating:
            header_lines.append(f"Rating: {prob.rating}")
        if prob.tags:
            header_lines.append(f"Tags: {', '.join(prob.tags)}")
        if header_lines:
            parts.append("\n".join(header_lines))
        if prob.statement:
            stmt = prob.statement[:_MAX_STMT_CHARS]
            suffix = "\n... (statement trimmed)" if len(prob.statement) > _MAX_STMT_CHARS else ""
            parts.append(f"Problem Statement:\n{stmt}{suffix}")

        if prob.examples:
            ex_lines = ["Sample tests (use these to verify code correctness):"]
            for i, ex in enumerate(prob.examples[:5]):
                inp = str(ex.get("input", ex.get("stdin", ""))).strip()
                out = str(ex.get("output", ex.get("stdout", ""))).strip()
                note = ex.get("note", "")
                line = f"  [{i + 1}] Input: {inp!r}  →  Expected output: {out!r}"
                if note:
                    line += f"  (Note: {note})"
                ex_lines.append(line)
            parts.append("\n".join(ex_lines))

    editor = req.effective_editor()
    parts.append(f"Language: {editor.language}")

    if editor.selected_text:
        parts.append(
            f"Selected code (near line {editor.cursor_line or '?'}):\n"
            f"```\n{editor.selected_text[:500]}\n```"
        )

    if editor.source_code.strip():
        lang_tag = editor.language.rstrip("0123456789")
        parts.append(f"Source code:\n```{lang_tag}\n{editor.source_code}\n```")
    else:
        parts.append("(No code written yet)")

    exec_ctx = req.effective_execution()
    status = exec_ctx.last_status
    if status and status not in ("Idle", "not_run"):
        exec_lines = [f"Last execution: {status}"]
        if exec_ctx.last_compile_output.strip():
            exec_lines.append(f"Compile output:\n{exec_ctx.last_compile_output[:_MAX_ERROR_CHARS]}")
        if exec_ctx.last_stderr.strip():
            exec_lines.append(f"Stderr:\n{exec_ctx.last_stderr[:_MAX_ERROR_CHARS]}")
        if exec_ctx.last_stdout.strip():
            exec_lines.append(f"Stdout:\n{exec_ctx.last_stdout[:500]}")
        if exec_ctx.last_expected_output.strip() and exec_ctx.last_actual_output.strip():
            exec_lines.append(f"Expected:\n{exec_ctx.last_expected_output[:300]}")
            exec_lines.append(f"Actual:\n{exec_ctx.last_actual_output[:300]}")
        if exec_ctx.last_input.strip():
            exec_lines.append(f"Input used:\n{exec_ctx.last_input[:200]}")
        parts.append("\n".join(exec_lines))

    if req.recent_events:
        recent = req.recent_events[-5:]
        lines = ["Recent activity:"]
        for ev in recent:
            line = f"  [{ev.type}]"
            if ev.summary:
                line += f" {ev.summary}"
            lines.append(line)
        parts.append("\n".join(lines))

    # Ground-truth evidence line — computed deterministically from exec_ctx,
    # never from the model's own claims. See _classify_execution_evidence.
    evidence = _classify_execution_evidence(exec_ctx)
    parts.append(f"[Verified execution evidence: {evidence}]")

    parts.append(f"User question: {req.message}")
    return "\n\n".join(parts)


# ─── Derived metadata ─────────────────────────────────────────────────────────

def _detect_issue_type(req: CopilotRequest, response: str) -> str | None:
    exec_ctx = req.effective_execution()
    status = exec_ctx.last_status.lower().replace(" ", "_")
    if "compilation" in status or exec_ctx.last_compile_output.strip():
        return "syntax"
    if "wrong_answer" in status or "wrong answer" in status:
        rl = response.lower()
        if any(w in rl for w in ("edge case", "boundary", "corner")):
            return "edge_case"
        if any(w in rl for w in ("overflow", "integer", "modulo", "mod ")):
            return "logic"
        return "logic"
    if "runtime" in status:
        return "logic"
    if "time_limit" in status or "tle" in status:
        return "complexity"
    if req.mode == "approach_review":
        return "approach"
    return None


def _suggest_next_action(req: CopilotRequest) -> str | None:
    exec_ctx = req.effective_execution()
    status = exec_ctx.last_status.lower().replace(" ", "_")
    if "compilation" in status:
        return "Fix the compilation error shown above, then run again."
    if "wrong_answer" in status or "wrong answer" in status:
        return "Add debug prints to trace intermediate values, or test n=0/n=1 edge cases."
    if "runtime" in status:
        return "Check array bounds, null references, or division by zero in your code."
    if "time_limit" in status:
        return "Profile which loop is slowest, then consider a more efficient algorithm or data structure."
    return None


# ─── DeepSeek API call ────────────────────────────────────────────────────────

async def _call_deepseek(
    settings: Any, user_content: str, max_tokens: int = 700
) -> tuple[str, str]:
    if not settings.deepseek_api_key:
        raise APIError(
            "copilot_not_configured",
            "AI Copilot is not configured. Add DEEPSEEK_API_KEY to the backend .env file.",
            status_code=503,
        )

    url = f"{settings.deepseek_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("deepseek http error: %d", exc.response.status_code)
            raise APIError(
                "copilot_provider_error",
                f"DeepSeek API returned HTTP {exc.response.status_code}. Check your API key.",
                status_code=502,
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("deepseek connection error: %s", type(exc).__name__)
            raise APIError(
                "copilot_provider_error",
                "Cannot reach DeepSeek API. Check DEEPSEEK_BASE_URL and network.",
                status_code=503,
            ) from exc

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    model_used = data.get("model", settings.deepseek_model)
    return content, model_used


# ─── Supabase persistence (best-effort) ──────────────────────────────────────

async def _sb_post(settings: Any, path: str, rows: list[dict] | dict, prefer: str = "return=minimal") -> None:
    """Fire-and-forget POST to Supabase REST API."""
    if not settings.supabase_url or not settings.supabase_service_key:
        return
    url = f"{settings.supabase_url}/rest/v1/{path}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, headers=headers, json=rows)
        except Exception as exc:
            logger.warning("supabase save failed (%s): %s", path, exc)


async def _persist(
    settings: Any,
    *,
    session_id: str,
    req: CopilotRequest,
    user_msg: str,
    assistant_msg: str,
    model: str,
    user_id: str | None,
) -> None:
    prob = req.effective_problem()
    editor = req.effective_editor()
    exec_ctx = req.effective_execution()

    # Upsert session row (ignore duplicate on conflict)
    await _sb_post(
        settings,
        "copilot_sessions",
        {
            "id": session_id,
            "user_id": user_id,
            "problem_id": (prob.id if prob else None) or req.problem_key,
            "contest_id": prob.contest_id if prob else None,
            "problem_index": prob.index if prob else None,
            "language": editor.language,
        },
        prefer="resolution=ignore-duplicates,return=minimal",
    )

    # Save user + assistant messages
    await _sb_post(
        settings,
        "copilot_messages",
        [
            {
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": user_msg[:10_000],
                "mode": req.mode,
                "help_level": req.help_level,
                "model": model,
                "consent_for_training": req.consent_for_training,
            },
            {
                "session_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": assistant_msg,
                "mode": req.mode,
                "help_level": req.help_level,
                "model": model,
                "consent_for_training": req.consent_for_training,
            },
        ],
    )

    # Save context snapshot only when consent given
    if req.consent_for_training:
        await _sb_post(
            settings,
            "copilot_context_snapshots",
            {
                "session_id": session_id,
                "problem_id": (prob.id if prob else None) or req.problem_key,
                "contest_id": prob.contest_id if prob else None,
                "problem_index": prob.index if prob else None,
                "language": editor.language,
                "source_code": _redact_secrets(editor.source_code)[:50_000] if editor.source_code else None,
                "selected_text": editor.selected_text,
                "cursor_line": editor.cursor_line,
                "last_status": exec_ctx.last_status,
                "last_stdout": exec_ctx.last_stdout[:2000] or None,
                "last_stderr": exec_ctx.last_stderr[:2000] or None,
                "last_compile_output": exec_ctx.last_compile_output[:2000] or None,
                "last_input": exec_ctx.last_input[:500] or None,
                "last_expected_output": exec_ctx.last_expected_output[:500] or None,
                "last_actual_output": exec_ctx.last_actual_output[:500] or None,
                "recent_events": [e.model_dump() for e in req.recent_events[-5:]],
                "consent_for_training": True,
            },
        )


# ─── Route ────────────────────────────────────────────────────────────────────

@router.post("/copilot", response_model=CopilotResponse)
async def copilot_chat(req: CopilotRequest, request: Request) -> CopilotResponse:
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    session_id = req.session_id or str(uuid.uuid4())
    settings = get_settings()
    user = auth.current_user(request)
    memory_user_id = user["user_id"] if user else None

    # ── Load coach profile (best-effort, never blocks on failure) ─────────────
    profile: dict | None = None
    if memory_user_id:
        try:
            profile = await load_profile(
                settings,
                user_id=memory_user_id,
                anonymous_user_key=None,
            )
        except Exception:
            pass

    # ── Build context message (with profile prepended if available) ───────────
    user_content = _build_context_message(req)
    if profile:
        profile_block = format_profile_for_prompt(profile)
        user_content = profile_block + "\n\n---\n\n" + user_content

    # Scale response length to help_level
    max_tokens = {1: 200, 2: 400, 3: 600, 4: 900, 5: 1400}.get(req.help_level, 600)

    assistant_content, model_used = await _call_deepseek(settings, user_content, max_tokens=max_tokens)

    # Enforce the evidence policy on the RAW model output before anything else
    # sees it — persistence, coach memory, and the API response all get the
    # policy-corrected message, never the unverified original.
    evidence = _classify_execution_evidence(req.effective_execution())
    assistant_content, evidence_type, verified_wrong = _enforce_evidence_policy(assistant_content, evidence)

    issue_type = _detect_issue_type(req, assistant_content)
    next_action = _suggest_next_action(req)

    await _persist(
        settings,
        session_id=session_id,
        req=req,
        user_msg=req.message,
        assistant_msg=assistant_content,
        model=model_used,
        user_id=memory_user_id,
    )

    # ── Save solving event for coach memory (best-effort) ─────────────────────
    if memory_user_id:
        try:
            exec_ctx = req.effective_execution()
            editor = req.effective_editor()
            prob = req.effective_problem()
            error_type = _coach_detect_error_type(
                compile_output=exec_ctx.last_compile_output,
                stderr=exec_ctx.last_stderr,
                status=exec_ctx.last_status,
            )
            event: dict = {
                "id": str(uuid.uuid4()),
                "user_id": memory_user_id,
                "anonymous_user_key": None,
                "session_id": session_id,
                "problem_id": (prob.id if prob else None) or req.problem_key,
                "contest_id": prob.contest_id if prob else None,
                "problem_index": prob.index if prob else None,
                "problem_title": prob.title if prob else None,
                "problem_rating": prob.rating if prob else None,
                "problem_tags": prob.tags if prob else [],
                "language": editor.language,
                "event_type": "copilot_question",
                "error_type": error_type,
                "short_summary": req.message[:200],
                "source_code_excerpt": (
                    _redact_secrets(editor.source_code[:500]) if editor.source_code else None
                ),
                "compiler_output_excerpt": (
                    _redact_secrets(exec_ctx.last_compile_output[:300])
                    if exec_ctx.last_compile_output else None
                ),
                "runtime_output_excerpt": (
                    _redact_secrets(exec_ctx.last_stderr[:300]) if exec_ctx.last_stderr else None
                ),
                "metadata": {
                    "mode": req.mode,
                    "help_level": req.help_level,
                    "last_status": exec_ctx.last_status,
                },
            }
            await save_solving_event(settings, event)
        except Exception:
            pass  # Non-fatal

    logger.info(
        "copilot: session=%s mode=%s level=%d lang=%s model=%s consent=%s profile=%s",
        session_id,
        req.mode,
        req.help_level,
        req.effective_editor().language,
        model_used,
        req.consent_for_training,
        "yes" if profile else "no",
    )

    return CopilotResponse(
        status="ok",
        message=assistant_content,
        session_id=session_id,
        model=model_used,
        suggested_next_action=next_action,
        detected_issue_type=issue_type,
        evidence_type=evidence_type,
        verified_wrong=verified_wrong,
    )
