from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.core.config import get_settings

_DAY_ID = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu",
}
_MONTH_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def get_now_info(timezone: str | None = None) -> dict:
    tz_name = timezone or get_settings().APP_TIMEZONE
    now = datetime.now(ZoneInfo(tz_name))
    day = _DAY_ID[now.strftime("%A")]
    month = _MONTH_ID[now.month]
    return {
        "iso": now.isoformat(),
        "timezone": tz_name,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_name": day,
        "human_date": f"{day}, {now.day} {month} {now.year}",
        "human_datetime": f"{day}, {now.day} {month} {now.year} pukul {now.strftime('%H:%M')} {tz_name}",
    }


@tool
def datetime_now() -> str:
    """Ambil tanggal dan waktu sekarang berdasarkan timezone aplikasi.

    Gunakan setiap kali user bertanya jam berapa, hari apa, atau tanggal berapa sekarang.
    """
    info = get_now_info()
    return f"Sekarang: *{info['human_datetime']}*\n\nISO: `{info['iso']}`"
