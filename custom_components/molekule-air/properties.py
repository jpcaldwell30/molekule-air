from enum import Enum, unique

@unique
class Mode(Enum):
    """Mode of operation."""
    auto = 0
    manual = 1

@unique
class Speed(Enum):
    """Fan speed."""
    Silent = 1
    Low = 2
    Medium = 3
    High = 4
    Turbo = 5
    SuperTurbo = 6

@unique
class Model(Enum):
    """Device model."""
    Molekule_Pro = "Molekule Pro" # 1
    Molekule_Mini_Plus = "Molekule Mini+" # 2
