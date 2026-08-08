from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path


def date_bound(value: str | None, end: bool = False) -> datetime | None:
    if value is None:
        return None
    text = value.strip().lower()
    now = datetime.now(UTC)
    if text == "today":
        base = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif text == "yesterday":
        base = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif text.endswith("d") and text[:-1].isdigit():
        base = (now - timedelta(days=int(text[:-1]))).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        parts = [int(part) for part in text.split("-")]
        base = datetime(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1, tzinfo=UTC)
    if not end:
        return base
    if text in {"today", "yesterday"} or text.endswith("d") or len(text.split("-")) == 3:
        return base + timedelta(days=1)
    if len(text.split("-")) == 2:
        return datetime(base.year + (base.month // 12), (base.month % 12) + 1, 1, tzinfo=UTC)
    return datetime(base.year + 1, 1, 1, tzinfo=UTC)


def parse_stamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        return None


def unix_seconds(value: float | None) -> str | None:
    return datetime.fromtimestamp(value, UTC).isoformat() if value is not None else None


def unix_millis(value: int | None) -> str | None:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat() if value is not None else None


def file_time(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
    except OSError:
        return None
