from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import Any


@dataclass(frozen=True)
class Offset:
    value: int
    unit: str

    def delta(self) -> timedelta:
        if self.unit == "minutes":
            return timedelta(minutes=self.value)
        if self.unit == "hours":
            return timedelta(hours=self.value)
        return timedelta(days=self.value)

    def label(self) -> str:
        unit_id = {"minutes": "menit", "hours": "jam", "days": "hari"}.get(self.unit, self.unit)
        return f"H-{self.value} {unit_id}"


class ReminderPolicy:
    @staticmethod
    def classify_priority(text: str) -> str:
        lowered = (text or "").casefold()
        if re.search(r"\b(urgent|mendesak|darurat|segera|hari ini)\b", lowered):
            return "urgent"
        if re.search(r"\b(deadline|dikumpulkan|tugas|ujian|quiz|kuis)\b", lowered):
            return "high"
        if re.search(r"\b(ide|opsional|santai)\b", lowered):
            return "low"
        return "normal"

    @staticmethod
    def infer_reminder_type(context: dict[str, Any]) -> str:
        if context.get("explicit"):
            return "explicit"
        source = str(context.get("source") or "")
        if source.startswith("goal"):
            return "auto_goal"
        if source.startswith("todo"):
            return "auto_todo"
        if source.startswith("planning"):
            return "auto_planning"
        if context.get("deadline_at"):
            return "deadline_offset"
        return "follow_up"

    @staticmethod
    def should_auto_create(context: dict[str, Any]) -> bool:
        text = (context.get("text") or "").casefold()
        if context.get("deadline_at"):
            return True
        if not context.get("remind_at"):
            return False
        if re.search(r"\b(deadline|dikumpulkan|tugas|todo|planning|proyek|project|besok|hari ini|nanti malam)\b", text):
            return True
        return False

    @staticmethod
    def default_offsets(context: dict[str, Any], now: datetime) -> list[Offset]:
        deadline = context.get("deadline_at")
        text = (context.get("text") or "").casefold()
        if not isinstance(deadline, datetime):
            return []

        if deadline <= now:
            return []
        if deadline - now < timedelta(hours=2):
            return [Offset(1, "minutes")]
        if deadline.date() == now.date():
            return [Offset(2, "hours")]

        academic = re.search(r"\b(tugas|kuliah|akademik|deadline|dikumpulkan|quiz|kuis|ujian|apsi|hebat)\b", text)
        if academic:
            return [Offset(1, "days"), Offset(2, "hours")]
        return [Offset(1, "hours")]

    @staticmethod
    def next_work_session(now: datetime, text: str = "") -> datetime:
        lowered = text.casefold()
        if "malam" in lowered:
            candidate = now.replace(hour=19, minute=0, second=0, microsecond=0)
        else:
            candidate = now.replace(hour=8, minute=0, second=0, microsecond=0)
        return candidate if candidate > now else candidate + timedelta(days=1)
