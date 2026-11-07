"""Input normalisation and validation for tracking numbers and postal codes.

bpost's lookup is very lenient: it ignores case and whitespace, accepts
trailing garbage such as "&x=1", "#x" or a backslash, and in testing did not
appear to verify the postal code. A successful lookup therefore says nothing
about whether the input was clean, so it is normalised and validated here
before anything is stored.
"""
from __future__ import annotations

import re

MAX_NAME_LENGTH = 100

_TRACKING_NUMBER_RE = re.compile(r"[A-Z0-9]{8,40}")
_POSTAL_CODE_RE = re.compile(r"[A-Z0-9][A-Z0-9 -]{1,8}[A-Z0-9]")


def normalize_tracking_number(value: str) -> str:
    """Remove all whitespace and upper-case, e.g. 'ca 5887 56303de' -> 'CA588756303DE'."""
    return "".join(value.split()).upper()


def normalize_postal_code(value: str) -> str:
    """Collapse whitespace and upper-case, e.g. ' 2830 ' -> '2830'."""
    return " ".join(value.split()).upper()


def is_valid_tracking_number(value: str) -> bool:
    """8-40 ASCII letters/digits (expects an already normalised value)."""
    return _TRACKING_NUMBER_RE.fullmatch(value) is not None


def is_valid_postal_code(value: str) -> bool:
    """3-10 ASCII letters/digits/spaces/hyphens (expects an already normalised value)."""
    return _POSTAL_CODE_RE.fullmatch(value) is not None
