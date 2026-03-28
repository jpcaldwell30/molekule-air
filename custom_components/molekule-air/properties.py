"""Shared enums for Molekule device data."""
from enum import Enum, IntEnum, unique


@unique
class Mode(str, Enum):
    """Supported Molekule operating modes."""

    smart = "smart"
    manual = "manual"


@unique
class Speed(IntEnum):
    """Fan speed values returned by Molekule."""

    Silent = 1
    Low = 2
    Medium = 3
    High = 4
    Turbo = 5
    SuperTurbo = 6


@unique
class Model(str, Enum):
    """Known Molekule device models."""

    Molekule_Pro = "Molekule Pro"
    Molekule_Mini_Plus = "Molekule Mini+"
