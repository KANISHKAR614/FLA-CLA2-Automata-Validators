"""Stage 3 of the validation architecture: semantic checks that run *after* a DFA accepts.

These are deliberately outside the automata (see report Sections 1.2 and 2.4).
The state-code table is an illustrative subset; production code must query the Vahan database.
"""

from __future__ import annotations

import datetime

# Illustrative list of two-letter Indian State/UT registration prefixes.
STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ", "HR", "HP", "JH", "JK",
    "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN",
    "TR", "TS", "UK", "UP", "WB",
}


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(month: int, year: int) -> int:
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def check_dob(text: str, today: datetime.date | None = None) -> tuple[bool, str]:
    """Assumes ``text`` already passed the DOB DFA."""
    today = today or datetime.date.today()
    day, month, year = int(text[0:2]), int(text[3:5]), int(text[6:10])
    if year < 1:
        return False, "year 0000 does not exist in the Gregorian calendar"
    if day > days_in_month(month, year):
        return False, f"month {month:02d} of {year} has only {days_in_month(month, year)} days"
    if datetime.date(year, month, day) > today:
        return False, "date of birth is in the future"
    return True, "calendar-valid"


def check_vehicle(text: str) -> tuple[bool, str]:
    """Assumes ``text`` already passed the vehicle DFA."""
    if text[:2] not in STATE_CODES:
        return False, f"unknown state/UT code {text[:2]!r}"
    if text[-4:] == "0000":
        return False, "serial number 0000 is not issued"
    return True, "state code known (RTO existence needs the Vahan database)"


def check_mobile(text: str) -> tuple[bool, str]:
    """Assumes ``text`` already passed the mobile DFA. Liveness needs an OTP / HLR lookup."""
    return True, "well-formed; send an OTP to confirm the line is active"
