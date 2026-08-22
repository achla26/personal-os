from datetime import datetime
from zoneinfo import ZoneInfo

# default timezone (New Zealand)
NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")


def now_nz() -> datetime:
    """Returns current datetime in New Zealand timezone (timezone-aware)."""
    return datetime.now(NZ_TIMEZONE)


def ensure_nz_tz(dt: datetime) -> datetime:
    """
    if datetime is naive (without timezone ),
    it assign NZ timezone.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=NZ_TIMEZONE)
    return dt.astimezone(NZ_TIMEZONE)