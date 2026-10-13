"""Deterministic keyword-based classification of academic task mental load."""
from __future__ import annotations

import re
from typing import Iterable

HIGH_LOAD_KEYWORDS = frozenset({
    "essay", "research", "analysis", "analyze", "proof", "derivation", "exam",
    "study", "programming", "coding", "design", "presentation", "project",
    "thesis", "report", "problem set", "calculus", "reading comprehension",
    "assignment", "homework", "lab", "algorithm", "debug", "solve", "write",
    "draft", "outline", "revise", "memorize", "chapter", "practice problems",
    "case study", "midterm", "final", "quiz prep",
})
LOW_LOAD_KEYWORDS = frozenset({
    "review notes", "flashcards", "整理", "organize notes", "organize", "format",
    "submit", "upload", "email", "print", "citation", "bibliography",
    "proofread", "copy", "schedule", "administrative", "quizlet", "tidy",
    "download", "register", "book", "reply",
})
MEDIUM_LOAD_KEYWORDS = frozenset({
    "read", "summarize", "summary", "practice", "prepare", "worksheet",
    "take notes", "study guide", "discussion", "language exercise",
})
# Long blocks of work with no keyword evidence are probably demanding.
LONG_TASK_MINUTES = 90

_WORD = re.compile(r"[\w]+(?:['’-][\w]+)*", re.UNICODE)


def _matches(text: str, keywords: Iterable[str]) -> set[str]:
    """Whole-word/phrase matches; a plural ``s`` is tolerated (essay/essays)."""
    normalized = " ".join(_WORD.findall(text.casefold()))
    found = set()
    for keyword in keywords:
        phrase = " ".join(_WORD.findall(keyword.casefold()))
        if phrase and re.search(rf"(?<!\w){re.escape(phrase)}(?:e?s)?(?!\w)", normalized):
            found.add(keyword)
    return found


def classify_task_detail(title: str, description: str = "", *, estimated_minutes=None,
                         high_keywords=None, low_keywords=None, default: str = "low") -> dict:
    """Return ``{"level", "confidence", "reason"}`` for a task.

    Title evidence counts double description evidence. Clear high/medium/low matches
    win; mixed or moderate matches are classified as medium load.
    """
    if default not in {"high", "medium", "low"}:
        raise ValueError("default must be 'high', 'medium', or 'low'")
    high_set = HIGH_LOAD_KEYWORDS | frozenset(high_keywords or ())
    low_set = LOW_LOAD_KEYWORDS | frozenset(low_keywords or ())
    t_high, t_low = _matches(title or "", high_set), _matches(title or "", low_set)
    d_high, d_low = _matches(description or "", high_set), _matches(description or "", low_set)
    high_w = 2 * len(t_high) + len(d_high - t_high)
    low_w = 2 * len(t_low) + len(d_low - t_low)
    t_medium = _matches(title or "", MEDIUM_LOAD_KEYWORDS)
    d_medium = _matches(description or "", MEDIUM_LOAD_KEYWORDS)
    medium_w = 2 * len(t_medium) + len(d_medium - t_medium)

    if high_w and high_w >= medium_w and high_w >= low_w - 1:
        found = sorted(t_high | d_high)
        conf = "high" if high_w >= 2 * max(low_w, medium_w, 1) else "medium"
        return {"level": "high", "confidence": conf, "reason": f"matches: {', '.join(found)}"}
    if low_w and low_w > high_w + 1 and low_w >= medium_w:
        return {"level": "low", "confidence": "high" if not high_w else "medium",
                "reason": f"matches: {', '.join(sorted(t_low | d_low))}"}
    if medium_w or (high_w and low_w):
        found = sorted(t_medium | d_medium | t_high | d_high | t_low | d_low)
        return {"level": "medium", "confidence": "medium" if found else "low",
                "reason": f"moderate or mixed workload: {', '.join(found)}"}
    if high_w:
        return {"level": "high", "confidence": "high",
                "reason": f"matches: {', '.join(sorted(t_high | d_high))}"}
    if low_w:
        return {"level": "low", "confidence": "high",
                "reason": f"matches: {', '.join(sorted(t_low | d_low))}"}
    try:
        minutes = int(estimated_minutes) if estimated_minutes is not None else None
    except (TypeError, ValueError):
        minutes = None
    if minutes is not None and minutes >= LONG_TASK_MINUTES:
        return {"level": "high", "confidence": "low",
                "reason": f"no keywords, but {minutes} min is a long block"}
    if minutes is not None and minutes >= 45:
        return {"level": "medium", "confidence": "low",
                "reason": f"no keywords, but {minutes} min is a moderate block"}
    return {"level": default, "confidence": "low", "reason": "no keywords matched"}


def classify_task(title: str, description: str = "", *, high_keywords=None,
                  low_keywords=None, default: str = "low", estimated_minutes=None) -> str:
    """Return ``high``, ``medium`` or ``low``.

    Matching uses whole words/phrases, so e.g. ``examined`` does not match
    ``exam``. Callers can provide additional keyword collections.
    """
    return classify_task_detail(title, description, estimated_minutes=estimated_minutes,
                                high_keywords=high_keywords, low_keywords=low_keywords,
                                default=default)["level"]
