"""Severity levels for rule engine findings."""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    """How serious a rule violation is."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
