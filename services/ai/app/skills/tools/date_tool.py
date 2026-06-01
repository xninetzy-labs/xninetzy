from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings

DAY_NAMES_ID = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu",
}

MONTH_NAMES_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


class DateTool:
    def now(self, timezone: str | None = None) -> dict[str, str | int]:
        tz_name = timezone or get_settings().APP_TIMEZONE
        now = datetime.now(ZoneInfo(tz_name))
        day_name = DAY_NAMES_ID[now.strftime("%A")]
        month_name = MONTH_NAMES_ID[now.month]

        return {
            "iso": now.isoformat(),
            "timezone": tz_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_name": day_name,
            "day": now.day,
            "month": now.month,
            "month_name": month_name,
            "year": now.year,
            "human_date": f"{day_name}, {now.day} {month_name} {now.year}",
            "human_datetime": f"{day_name}, {now.day} {month_name} {now.year} pukul {now.strftime('%H:%M')} {tz_name}",
        }
