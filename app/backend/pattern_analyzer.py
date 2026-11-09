"""Local, deterministic analysis of repeated study-session outcomes."""
from collections import defaultdict
from datetime import datetime
from statistics import mean

MIN_PATTERN_SESSIONS = 4


def analyze_patterns(sessions, *, min_sessions=MIN_PATTERN_SESSIONS):
    """Return evidence-backed recommendations; missing fields are ignored per metric."""
    rows = [dict(x) for x in sessions if x is not None]
    findings = []
    def finding(key, title, evidence, n, confidence):
        findings.append({"key": key, "recommendation": title, "evidence": evidence,
                         "samples": n, "confidence": confidence})
    def rows_with(predicate):
        return [r for r in rows if predicate(r)]
    low = rows_with(lambda r: _num(r.get("energy")) is not None and _num(r.get("energy")) <= 2)
    medium_success = [r for r in low if str(r.get("load_level", "")).lower() == "medium" and _successful(r)]
    if len(medium_success) >= min_sessions:
        finding("low_energy_medium", "You often complete medium-load tasks during low-energy periods. Consider starting with one of these tasks.",
                f"{len(medium_success)} of {len(low)} low-energy sessions with medium-load tasks were completed.", len(medium_success), _confidence(len(medium_success)))
    high = rows_with(lambda r: _num(r.get("energy")) is not None and _num(r.get("energy")) >= 4)
    high_stops = [r for r in high if not _successful(r)]
    if len(high_stops) >= min_sessions and len(high) >= min_sessions and len(high_stops) / len(high) >= .6:
        finding("high_energy_stops", "You often leave sessions unfinished even when reporting high energy. Consider shorter blocks or checking task difficulty before starting.",
                f"{len(high_stops)} of {len(high)} high-energy sessions were unfinished.", len(high), _confidence(len(high)))
    hard = [r for r in rows if _num(r.get("perceived_difficulty")) is not None]
    difficult = [r for r in hard if _num(r["perceived_difficulty"]) >= 4]
    easy = [r for r in hard if _num(r["perceived_difficulty"]) <= 2]
    if len(difficult) >= min_sessions and len(easy) >= min_sessions and _rate(difficult) >= _rate(easy) + .2:
        finding("difficulty_success", "You tend to complete tasks you rate as difficult. Consider scheduling one demanding task when you have a clear block of time.",
                f"Completion was {_pct(difficult)} for difficult tasks versus {_pct(easy)} for easier tasks.", len(hard), _confidence(len(hard)))
    high_load = rows_with(lambda r: str(r.get("load_level", "")).lower() == "high" and r.get("started_at"))
    mornings = [r for r in high_load if _hour(r.get("started_at")) is not None and 5 <= _hour(r.get("started_at")) < 12]
    other = [r for r in high_load if r not in mornings]
    if len(mornings) >= min_sessions and len(other) >= min_sessions and _rate(mornings) >= _rate(other) + .2:
        finding("morning_demanding", "Your history suggests you complete demanding tasks more consistently in the morning.",
                f"Completion was {_pct(mornings)} in morning sessions versus {_pct(other)} at other times.", len(high_load), _confidence(len(high_load)))
    duration = [r for r in rows if not r.get("interrupted") and _num(r.get("planned_minutes"))
                and _num(r.get("actual_minutes"))]
    if len(duration) >= min_sessions and mean(_num(r["actual_minutes"]) / _num(r["planned_minutes"]) for r in duration) < .75:
        finding("shorter_sessions", "Your planned study sessions are usually longer than your actual sessions. Consider trying shorter blocks.",
                f"Across {len(duration)} sessions, actual duration averaged {mean(_num(r['actual_minutes']) / _num(r['planned_minutes']) for r in duration):.0%} of planned duration.", len(duration), _confidence(len(duration)))
    return {"recommendations": findings, "sessions_analyzed": len(rows)}


def _num(x):
    try: return float(x) if x is not None else None
    except (TypeError, ValueError): return None


def _successful(r):
    return bool(r.get("completed")) or str(r.get("outcome", "")).lower() in {"completed", "success"}


def _hour(x):
    try: return datetime.fromisoformat(str(x).replace("Z", "+00:00")).hour
    except (ValueError, TypeError): return None


def _rate(rows): return sum(_successful(r) for r in rows) / len(rows) if rows else 0

def _pct(rows): return f"{_rate(rows):.0%}"

def _confidence(n): return "high" if n >= 10 else "medium" if n >= 6 else "low"
