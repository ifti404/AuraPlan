"""Shared task data model used by storage and scheduling modules."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    title: str
    deadline: str
    estimated_minutes: int
    description: str = ""
    load_level: str = "high"
    status: str = "pending"
    id: Optional[int] = None
    scheduled_date: Optional[str] = None
