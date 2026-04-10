"""Shared enums for Molekule device data."""
from enum import IntEnum, unique


@unique
class Speed(IntEnum):
    """Fan speed values returned by Molekule."""

    Silent = 1
    Low = 2
    Medium = 3
    High = 4
    Turbo = 5
    SuperTurbo = 6
