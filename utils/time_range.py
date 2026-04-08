"""
Parse optional audio segment ranges like ``2:00 - 4:56``, ``start - 6:47``, ``4:56 - end``.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

__all__ = ["parse_time_range_line", "format_range_hint"]


def _normalize_overflow(parts: list[float]) -> list[int]:
    """Carry overflow so seconds/minutes stay in 0–59 where appropriate."""
    if len(parts) == 2:
        m, s = int(parts[0]), parts[1]
        extra_m, s = divmod(int(s), 60)
        m += extra_m
        return [m, int(s)]
    if len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), parts[2]
        extra_m, s = divmod(int(s), 60)
        m += extra_m
        extra_h, m = divmod(m, 60)
        h += extra_h
        return [h, m, int(s)]
    return [int(p) for p in parts]


def _parse_clock(s: str) -> float:
    """Parse H:M:S, M:S, or plain seconds.
    Also accepts:
    - 300 → 3:00
    - 1233 → 12:33
    - 458 → 4:58
    - 0908 → 9:08
    """
    s = s.strip().lower()
    if not s:
        raise ValueError("empty time")
    # Numeric shorthand (no colons)
    if re.match(r"^\d+$", s):
        val = int(s)
        if val == 0:
            return 0.0
        if val < 100:
            # 0-99: plain seconds
            return float(val)
        # 3+ digits: treat as MMSS format
        seconds = val % 100
        minutes = val // 100
        return float(minutes * 60 + seconds)
    if re.match(r"^\d+(\.\d+)?$", s):
        return float(s)
    parts = s.split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"invalid time: {s!r}")
    nums = [float(p) for p in parts]
    fixed = _normalize_overflow(nums)
    if len(fixed) == 2:
        return fixed[0] * 60 + fixed[1]
    return fixed[0] * 3600 + fixed[1] * 60 + fixed[2]


def _parse_start_token(tok: str) -> float:
    t = tok.strip().lower()
    if not t or t in ("start", "begin", "0"):
        return 0.0
    return _parse_clock(t)


def _parse_end_token(tok: str) -> Optional[float]:
    t = tok.strip().lower()
    if not t or t == "end":
        return None
    return _parse_clock(t)


def parse_time_range_line(line: str) -> Optional[Tuple[float, Optional[float]]]:
    """
    Parse a single line ``left - right``.

    Returns:
        ``None`` — empty line, use full source length.
        ``(start_sec, end_sec)`` — ``end_sec`` is ``None`` to mean end of file.

    Raises:
        ValueError: invalid format or end before start.
    """
    raw = line.strip()
    if not raw:
        return None

    if "-" not in raw:
        raise ValueError('Use the form: start - end   (example: 2:00 - 4:56)')

    m = re.match(r"^\s*(.*?)\s*-\s*(.*)\s*$", raw)
    if not m:
        raise ValueError('Use the form: start - end   (example: 2:00 - 4:56)')

    left, right = m.group(1).strip(), m.group(2).strip()
    start = _parse_start_token(left)
    end = _parse_end_token(right)

    if end is not None and end <= start:
        raise ValueError("End time must be after start time.")

    return (start, end)


def format_range_hint() -> str:
    return "e.g. 2:00 - 4:56, start - 6:47, 4:56 - end"
