from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_interview_day_bounds(
    tz_str: str | None, now_utc: datetime | None = None
) -> tuple[datetime, datetime]:
    """Calculates the UTC bounds [start_utc, end_utc) for the current 4:00 AM interview day.

    The interview day resets daily at 4:00 AM in the student's local IANA timezone.
    Pure calculation logic.
    """
    if not tz_str:
        tz_str = "UTC"

    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("UTC")

    if now_utc is None:
        now_utc = datetime.now(ZoneInfo("UTC"))
    elif now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=ZoneInfo("UTC"))

    local_now = now_utc.astimezone(tz)
    cutoff_today = local_now.replace(hour=4, minute=0, second=0, microsecond=0)

    if local_now < cutoff_today:
        start_local = cutoff_today - timedelta(days=1)
        end_local = cutoff_today
    else:
        start_local = cutoff_today
        end_local = cutoff_today + timedelta(days=1)

    start_utc = start_local.astimezone(ZoneInfo("UTC"))
    end_utc = end_local.astimezone(ZoneInfo("UTC"))
    return start_utc, end_utc
