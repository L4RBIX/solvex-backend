"""Parse official Codeforces problem-page HTML into SolveX content dicts.

Output shape matches ``problem_content.json`` entries expected by
``problem_import._classify`` / ``_validate_content_entry``:

- title, description, input_format, output_format, interaction_format
- note, examples[{input,output}], time/memory limits, input_mode
- source, source_url, asset_required, picture_count

SECURITY: this module never reads or emits editorials, solutions, or
reference code. It only extracts the public ``.problem-statement`` region.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

SOURCE_DATASET = "codeforces-official-page"

_SKIP_TAGS = frozenset({"script", "style", "noscript", "svg"})
_CLOUDFLARE_MARKERS = (
    "just a moment",
    "cf-chl",
    "challenge-platform",
    "enable javascript and cookies to continue",
    "checking your browser before accessing",
)
_ERROR_MARKERS = (
    "page not found",
    "contest is not available",
    "you are not allowed to view",
    "login into codeforces",
)


@dataclass
class ParsedStatement:
    content: dict[str, Any]
    contest_id: int
    index: str
    picture_count: int
    warnings: list[str]


class StatementParseError(ValueError):
    """Raised when HTML is not a usable public Codeforces problem statement."""


def is_cloudflare_or_challenge_page(html: str) -> bool:
    lowered = (html or "")[:8000].lower()
    return any(marker in lowered for marker in _CLOUDFLARE_MARKERS)


def is_error_or_login_page(html: str) -> bool:
    lowered = (html or "").lower()
    if "problem-statement" in lowered:
        return False
    return any(marker in lowered for marker in _ERROR_MARKERS)


def official_problem_url(contest_id: int, index: str) -> str:
    return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"


def _clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u2009", " ").replace("\u200b", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _node_to_text(node: Any) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    if node.name in _SKIP_TAGS:
        return ""
    if node.name == "br":
        return "\n"
    if node.name == "img":
        return ""
    if node.name == "li":
        inner = "".join(_node_to_text(child) for child in node.children).strip()
        return f"- {inner}\n" if inner else ""

    parts = [_node_to_text(child) for child in node.children]
    text = "".join(parts)
    classes = node.get("class") or []
    if "test-example-line" in classes:
        return text
    if node.name in {"p", "div", "h1", "h2", "h3", "h4", "tr", "section"}:
        text = text.strip("\n")
        return f"{text}\n\n" if text else ""
    return text


def _fragment_text(element: Tag | None, *, drop_titles: bool = True) -> str:
    if element is None:
        return ""
    clone = BeautifulSoup(str(element), "lxml")
    root = clone.find(True)
    if root is None:
        return ""
    if drop_titles:
        for title in root.select(".section-title, .title"):
            title.decompose()
    return _clean_text(_node_to_text(root))


def _sample_pre_text(pre: Tag) -> str:
    lines = pre.select(".test-example-line")
    if lines:
        return "\n".join(line.get_text() for line in lines)
    working = BeautifulSoup(str(pre), "lxml")
    node = working.find("pre") or working
    for br in node.find_all("br"):
        br.replace_with("\n")
    return node.get_text()


def _parse_limits(header: Tag) -> tuple[float | None, float | None, str | None]:
    time_limit = None
    memory_limit = None
    io_mode = "stdio"

    tl = header.select_one(".time-limit")
    if tl is not None:
        match = re.search(r"([\d.]+)\s*second", tl.get_text(" ", strip=True), re.I)
        if match:
            time_limit = float(match.group(1))

    ml = header.select_one(".memory-limit")
    if ml is not None:
        match = re.search(r"([\d.]+)\s*megabyte", ml.get_text(" ", strip=True), re.I)
        if match:
            memory_limit = float(match.group(1))

    input_file = header.select_one(".input-file")
    output_file = header.select_one(".output-file")
    for node in (input_file, output_file):
        if node is None:
            continue
        text = node.get_text(" ", strip=True).lower()
        classes = node.get("class") or []
        if "input-standard" in classes or "output-standard" in classes:
            continue
        if "standard" in text or "stdin" in text or "stdout" in text:
            continue
        # Named files (e.g. "input input.txt") imply file I/O.
        if ".txt" in text or "file" in text:
            io_mode = "file"

    return time_limit, memory_limit, io_mode


def _extract_index_from_title(title_text: str) -> str | None:
    match = re.match(r"^([A-Za-z][A-Za-z0-9]*)\.", title_text.strip())
    return match.group(1) if match else None


def _strip_index_prefix(title_text: str) -> str:
    return re.sub(r"^[A-Za-z][A-Za-z0-9]*\.\s*", "", title_text.strip()).strip()


def parse_codeforces_problem_html(
    html: str,
    *,
    expected_contest_id: int,
    expected_index: str,
) -> ParsedStatement:
    if not html or not html.strip():
        raise StatementParseError("empty HTML response")
    if is_cloudflare_or_challenge_page(html):
        raise StatementParseError("cloudflare or browser-challenge page")
    if is_error_or_login_page(html):
        raise StatementParseError("error or login page")

    soup = BeautifulSoup(html, "lxml")
    problem = soup.select_one(".problem-statement")
    if problem is None:
        raise StatementParseError("missing .problem-statement")

    # Reject editorial pages that somehow include a statement fragment.
    page_text_head = soup.get_text(" ", strip=True)[:500].lower()
    if "editorial" in page_text_head and "problem-statement" not in html[:2000].lower():
        raise StatementParseError("editorial page rejected")

    header = problem.select_one(".header")
    if header is None:
        raise StatementParseError("missing statement header")

    title_node = header.select_one(".title")
    if title_node is None:
        raise StatementParseError("missing statement title")
    title_text = title_node.get_text(" ", strip=True)
    parsed_index = _extract_index_from_title(title_text)
    expected_index_norm = expected_index.strip().upper()
    if parsed_index and parsed_index.upper() != expected_index_norm:
        raise StatementParseError(
            f"index mismatch: page={parsed_index!r} expected={expected_index_norm!r}"
        )

    # Soft identity check via document title when present.
    doc_title = (soup.title.get_text(" ", strip=True) if soup.title else "").upper()
    expected_token = f"{expected_contest_id}{expected_index_norm}".upper()
    if doc_title and expected_token not in doc_title.replace(" ", ""):
        # Some mirrors omit the id; require the statement body instead.
        if len(_fragment_text(problem)) < 40:
            raise StatementParseError("document title identity mismatch")

    time_limit, memory_limit, io_mode = _parse_limits(header)
    picture_count = len(problem.select("img"))
    warnings: list[str] = []

    statement_parts: list[str] = []
    interaction: str | None = None
    for child in problem.find_all(recursive=False):
        if not isinstance(child, Tag):
            continue
        classes = child.get("class") or []
        if "header" in classes:
            continue
        if any(
            key in classes
            for key in (
                "input-specification",
                "output-specification",
                "sample-tests",
                "note",
            )
        ):
            continue
        section_title = child.select_one(".section-title")
        section_name = section_title.get_text(" ", strip=True).lower() if section_title else ""
        text = _fragment_text(child)
        if not text:
            continue
        if section_name == "interaction" or "interaction" in classes:
            interaction = text
            continue
        statement_parts.append(text)

    statement = _clean_text("\n\n".join(statement_parts))
    if len(statement) < 40:
        raise StatementParseError("statement text too short")

    input_format = _fragment_text(problem.select_one(".input-specification")) or None
    output_format = _fragment_text(problem.select_one(".output-specification")) or None
    notes = _fragment_text(problem.select_one(".note")) or None

    examples: list[dict[str, str]] = []
    for block in problem.select(".sample-tests .sample-test"):
        input_pre = block.select_one(".input pre")
        output_pre = block.select_one(".output pre")
        if input_pre is None or output_pre is None:
            warnings.append("sample block missing pre")
            continue
        examples.append(
            {
                "input": _sample_pre_text(input_pre).strip("\n"),
                "output": _sample_pre_text(output_pre).strip("\n"),
            }
        )

    if not examples and not interaction:
        warnings.append("no public samples parsed")

    # Interactive problems often state it in the body even without a section.
    if interaction is None and re.search(r"\binteractive problem\b", statement, re.I):
        warnings.append("interactive mentioned without interaction section")

    asset_required = picture_count > 0
    if asset_required:
        warnings.append(f"{picture_count} statement image(s) not ingested")

    content = {
        "title": _strip_index_prefix(title_text) or title_text,
        "description": statement,
        "input_format": input_format,
        "output_format": output_format,
        "interaction_format": interaction,
        "note": notes,
        "examples": examples,
        "time_limit_seconds": time_limit,
        "memory_limit_megabytes": memory_limit,
        "input_mode": io_mode,
        "source": SOURCE_DATASET,
        "source_url": official_problem_url(expected_contest_id, expected_index_norm),
        "sources": [official_problem_url(expected_contest_id, expected_index_norm)],
        "asset_required": asset_required,
        "picture_count": picture_count,
        # Never populate editorial / reference_code — keys intentionally absent.
    }
    return ParsedStatement(
        content=content,
        contest_id=expected_contest_id,
        index=expected_index_norm,
        picture_count=picture_count,
        warnings=warnings,
    )
