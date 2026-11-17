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


def _phrase(text: str) -> str:
    return " ".join(_WORD.findall(text.casefold()))


def _pattern(phrase: str) -> str:
    """Regex for a phrase that tolerates simple plurals (essay/essays, study/studies)."""
    if len(phrase) > 1 and phrase.endswith("y") and phrase[-2] not in "aeiou":
        return re.escape(phrase[:-1]) + r"(?:y|ies)"
    return re.escape(phrase) + r"(?:e?s)?"


def _matches(text: str, keywords: Iterable[str]) -> set[str]:
    """Whole-word/phrase matches; simple plurals are tolerated."""
    normalized = _phrase(text)
    found = set()
    for keyword in keywords:
        phrase = _phrase(keyword)
        if phrase and re.search(rf"(?<!\w){_pattern(phrase)}(?!\w)", normalized):
            found.add(keyword)
    return found


def _found(text: str, groups: dict) -> dict:
    """Matches per level, dropping a keyword that is only part of a longer matched
    phrase (so "study guide" is not also counted as "study")."""
    found = {level: _matches(text, words) for level, words in groups.items()}
    phrases = {kw: _phrase(kw) for matched in found.values() for kw in matched}
    for matched in found.values():
        for kw in list(matched):
            inner = f" {phrases[kw]} "
            if any(other != kw and phrases[other] != phrases[kw] and inner in f" {phrases[other]} "
                   for other in phrases):
                matched.discard(kw)
    return found


def _leads(normalized_title: str, keywords) -> bool:
    """True when the title starts with one of the keywords (usually its action verb)."""
    return any(re.match(rf"{_pattern(_phrase(kw))}(?!\w)", normalized_title) for kw in keywords)


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
    groups = {"high": high_set, "medium": MEDIUM_LOAD_KEYWORDS, "low": low_set}
    title_found = _found(title or "", groups)
    desc_found = _found(description or "", groups)
    title_norm = _phrase(title or "")

    def weight(level):
        # Title evidence counts double. A light administrative verb that opens the
        # title is the real action ("Submit assignment", "Email TA about homework"),
        # so it counts extra against the nouns that follow it.
        lead = 2 if level == "low" and _leads(title_norm, title_found[level]) else 0
        return 2 * len(title_found[level]) + len(desc_found[level] - title_found[level]) + lead

    t_high, t_medium, t_low = title_found["high"], title_found["medium"], title_found["low"]
    d_high, d_medium, d_low = desc_found["high"], desc_found["medium"], desc_found["low"]
    high_w, medium_w, low_w = weight("high"), weight("medium"), weight("low")

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
