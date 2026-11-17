"""Backend tests. Run from the project root: python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "backend"))

from planner import plan_week
from priority_engine import score_breakdown
from scheduler import generate_schedule
from task_classifier import classify_task, classify_task_detail
from task_repository import TaskRepository

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)


def task(id, title, hours, minutes, load="medium", status="pending"):
    deadline = None if hours is None else (NOW + timedelta(hours=hours)).isoformat()
    return {"id": id, "title": title, "deadline": deadline, "estimated_minutes": minutes,
            "load_level": load, "status": status}


class ClassifierTests(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(classify_task("Write history essay"), "high")
        self.assertEqual(classify_task("Email professor"), "low")
        self.assertEqual(classify_task("Make study guide"), "medium")

    def test_whole_words_only(self):
        self.assertEqual(classify_task("Examined notes"), "low")

    def test_plurals(self):
        self.assertEqual(classify_task("Write case studies"), "high")
        self.assertEqual(classify_task("Read essays"), "high")

    def test_leading_admin_verb_wins(self):
        self.assertEqual(classify_task("Submit assignment"), "low")
        self.assertEqual(classify_task("Email TA about homework"), "low")

    def test_overlapping_keywords_counted_once(self):
        reason = classify_task_detail("Organize notes")["reason"]
        self.assertNotIn("organize,", reason)

    def test_duration_fallback(self):
        self.assertEqual(classify_task("Misc", estimated_minutes=100), "high")
        self.assertEqual(classify_task("Misc", estimated_minutes=50), "medium")


class PriorityTests(unittest.TestCase):
    def test_worked_example(self):
        score = score_breakdown(task(1, "A", 6, 90, "high"), now=NOW, energy=3)["score"]
        self.assertAlmostEqual(score, 128.75)

    def test_low_energy_cannot_bury_urgent_task(self):
        urgent = score_breakdown(task(1, "A", 6, 90, "high"), now=NOW, energy=1)["score"]
        relaxed = score_breakdown(task(2, "B", 120, 30, "low"), now=NOW, energy=1)["score"]
        self.assertGreater(urgent, relaxed)

    def test_done_tasks_are_ignored(self):
        self.assertEqual(score_breakdown(task(1, "A", 6, 30, status="completed"), now=NOW)["score"],
                         float("-inf"))

    def test_energy_range(self):
        with self.assertRaises(ValueError):
            score_breakdown(task(1, "A", 6, 30), now=NOW, energy=0)


class SchedulerTests(unittest.TestCase):
    def test_short_urgent_budget_defers_second_task(self):
        plan = generate_schedule([task(1, "A", 6, 90, "high"), task(2, "B", 40, 120, "low")],
                                 available_minutes=100, now=NOW)
        self.assertEqual([t["title"] for t in plan["scheduled"]], ["A"])
        self.assertEqual([t["title"] for t in plan["deferred"]], ["B"])
        self.assertEqual([t["title"] for t in plan["at_risk"]], ["B"])

    def test_partial_block(self):
        plan = generate_schedule([task(1, "A", 6, 90, "high")], available_minutes=40, now=NOW)
        self.assertTrue(plan["scheduled"][0]["partial"])
        self.assertEqual(plan["scheduled"][0]["scheduled_minutes"], 40)


class PlannerTests(unittest.TestCase):
    def test_overdue_earlier_today_is_late_not_at_risk(self):
        plan = plan_week([task(1, "Overdue", -3, 60, "low")], daily_minutes=0, now=NOW)
        self.assertEqual([t["title"] for t in plan["late"]], ["Overdue"])
        self.assertEqual(plan["at_risk"], [])

    def test_future_task_that_cannot_fit_is_at_risk(self):
        plan = plan_week([task(1, "Later", 2, 60, "high")], daily_minutes=0, now=NOW)
        self.assertEqual([t["title"] for t in plan["at_risk"]], ["Later"])
        self.assertEqual(plan["late"], [])

    def test_long_task_is_split_across_days(self):
        plan = plan_week([task(1, "Big", 24 * 5, 240, "high")], daily_minutes=120, now=NOW)
        used = [d["used_minutes"] for d in plan["days"]]
        self.assertEqual(sum(used), 240)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.sqlite3")
        self.repo = TaskRepository(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_crud_and_persistence(self):
        t = self.repo.create_task(title="Essay", deadline="2026-11-20T10:00:00+06:00",
                                  estimated_minutes=90, load_level="medium")
        self.assertEqual(TaskRepository(self.path).get_task(t.id).title, "Essay")
        self.assertEqual(self.repo.update_task(t.id, status="completed").status, "completed")
        self.assertTrue(self.repo.delete_task(t.id))
        self.assertIsNone(self.repo.get_task(t.id))

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.repo.create_task(title=" ", deadline="2026-11-20T10:00:00", estimated_minutes=5)
        with self.assertRaises(ValueError):
            self.repo.create_task(title="x", deadline="not a date", estimated_minutes=5)
        with self.assertRaises(ValueError):
            self.repo.create_task(title="x", deadline="2026-11-20T10:00:00", estimated_minutes=-1)

    def test_updated_at_matches_created_at_format(self):
        import sqlite3
        t = self.repo.create_task(title="x", deadline="2026-11-20T10:00:00", estimated_minutes=5)
        self.repo.update_task(t.id, title="y")
        row = sqlite3.connect(self.path).execute(
            "SELECT created_at, updated_at FROM tasks WHERE id = ?", (t.id,)).fetchone()
        self.assertTrue(row[0].endswith("Z") and row[1].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
