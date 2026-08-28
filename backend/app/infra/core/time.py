from datetime import datetime
from zoneinfo import ZoneInfo

# default timezone (New Zealand)
CURRENT_TIMEZONE = ZoneInfo("Pacific/Auckland")


def now_nz() -> datetime:
    """Returns current datetime in New Zealand timezone (timezone-aware)."""
    return datetime.now(CURRENT_TIMEZONE)


def ensure_nz_tz(dt: datetime) -> datetime:
    """
    if datetime is naive (without timezone ),
    it assign NZ timezone.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=CURRENT_TIMEZONE)
    return dt.astimezone(CURRENT_TIMEZONE)


def now_local_tz(tz) -> datetime:
    """Returns current datetime in given timezone (timezone-aware)."""
    return datetime.now(tz)