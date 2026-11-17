"""Local profile registry for separating AuraPlan workspaces on one device."""
from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from database import DEFAULT_DB_PATH


class ProfileStore:
    """Persist profile names and map each profile to its own SQLite database."""

    DEFAULT_PROFILE = {"id": "default", "name": "Default"}

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else DEFAULT_DB_PATH.parent
        self.registry_path = self.root / "profiles.json"
        self.profile_root = self.root / "profiles"
        self.root.mkdir(parents=True, exist_ok=True)
        self._profiles = self._read()

    def _read(self) -> list[dict[str, str]]:
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            profiles = data.get("profiles") if isinstance(data, dict) else None
            if isinstance(profiles, list):
                valid = [item for item in profiles if isinstance(item, dict)
                         and isinstance(item.get("id"), str)
                         and isinstance(item.get("name"), str)
                         and item["name"].strip()]
                if valid:
                    if not any(item["id"] == "default" for item in valid):
                        valid.insert(0, self.DEFAULT_PROFILE.copy())
                    return valid
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        # The original AuraPlan database remains available as the Default profile.
        profiles = [self.DEFAULT_PROFILE.copy()]
        self._write(profiles)
        return profiles

    def _write(self, profiles: list[dict[str, str]]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp_path = self.registry_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps({"profiles": profiles}, indent=2) + "\n",
                             encoding="utf-8")
        os.replace(temp_path, self.registry_path)

    def list_profiles(self) -> list[dict[str, str]]:
        return [profile.copy() for profile in self._profiles]

    def create_profile(self, name: str) -> dict[str, str]:
        clean_name = " ".join(str(name).split())
        if not clean_name:
            raise ValueError("Enter a profile name.")
        if len(clean_name) > 32:
            raise ValueError("Profile names must be 32 characters or fewer.")
        if any(p["name"].casefold() == clean_name.casefold() for p in self._profiles):
            raise ValueError("A profile with that name already exists.")
        profile = {"id": uuid4().hex, "name": clean_name}
        updated = [*self._profiles, profile]
        self._write(updated)
        self._profiles = updated
        return profile.copy()

    def database_path(self, profile_id: str) -> Path:
        profile = next((item for item in self._profiles if item["id"] == profile_id), None)
        if profile is None:
            raise ValueError("Choose a profile that exists on this device.")
        if profile_id == "default":
            return DEFAULT_DB_PATH
        return self.profile_root / profile_id / "auraplan.sqlite3"
