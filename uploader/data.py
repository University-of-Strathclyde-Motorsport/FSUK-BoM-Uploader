"""
This module contains data structures and validation functions for Bill of Materials data.
"""

from dataclasses import InitVar, dataclass, field
from enum import StrEnum
from typing import Optional

VALID_MAKE_OR_BUY = ["Make", "Buy"]
VALID_STEP_TYPES = ["Material", "Process", "Fasteners", "Tooling"]
MAXIMUM_QUANTITY = 999


class RowType(StrEnum):
    """Enum of valid row types."""

    SYSTEM = "System"
    ASSEMBLY = "Assembly"
    PART = "Part"
    STEP = "Step"
    UNDEFINED = "Undefined"


class FSUKSystems(StrEnum):
    """Enum of valid FSUK systems."""

    BR = "Brake System"
    FR = "Chassis and Body"
    DT = "Drivetrain"
    TS = "Engine and Tractive System"
    EL = "Grounded Low Voltage System"
    MS = "Miscellaneous"
    ST = "Steering System"
    SU = "Suspension System"
    WT = "Wheels and Tyres"


FSUK_SYSTEM_MAP: dict[str, FSUKSystems] = {
    "Brakes": FSUKSystems.BR,
    "Chassis & Body": FSUKSystems.FR,
    "Drivetrain": FSUKSystems.DT,
    "Engine & TS": FSUKSystems.TS,
    "Electrical": FSUKSystems.EL,
    "Misc": FSUKSystems.MS,
    "Steering": FSUKSystems.ST,
    "Suspension": FSUKSystems.SU,
    "Wheels": FSUKSystems.WT,
}


def _determine_fsuk_system(system: str) -> FSUKSystems:
    """Determine the FSUK system from a string."""
    if system in FSUKSystems.__members__:
        return FSUKSystems(system)
    if system in FSUK_SYSTEM_MAP.keys():
        return FSUK_SYSTEM_MAP[system]
    raise KeyError(f"Invalid system '{system}'")


@dataclass
class RowData(object):
    """A row of data in the Bill of Materials."""

    system: InitVar[str]
    assembly: str
    part: str
    make_or_buy: str
    step_type: str
    subtype: str
    comment: str
    quantity: int
    cost: float
    cost_comment: str
    carbon_footprint: float
    carbon_comment: str
    fsuk_system: Optional[FSUKSystems] = field(init=False)

    def __post_init__(self, system: str) -> None:
        if system:
            self.fsuk_system = _determine_fsuk_system(system)
        else:
            self.fsuk_system = None

    @property
    def row_type(self) -> RowType:
        if self.fsuk_system is not None:
            row_type = RowType.SYSTEM
        elif self.assembly != "":
            row_type = RowType.ASSEMBLY
        elif self.part != "":
            row_type = RowType.PART
        elif self.step_type != "":
            row_type = RowType.STEP
        else:
            row_type = RowType.UNDEFINED

        return row_type

    def requires_quantity(self) -> bool:
        return self.row_type in [RowType.PART, RowType.STEP]

    def __str__(self) -> str:
        """Get a string identifier for the row."""
        match self.row_type:
            case RowType.SYSTEM:
                identifier = self.fsuk_system if self.fsuk_system else ""
            case RowType.ASSEMBLY:
                identifier = self.assembly
            case RowType.PART:
                identifier = self.part
            case RowType.STEP:
                identifier = f"{self.step_type}: {self.subtype}"
            case _:
                identifier = "Invalid row"
        return identifier


@dataclass
class Cursor(object):
    """Dataclass holding information about where to upload rows."""

    system: Optional[FSUKSystems] = None
    assembly: Optional[str] = None
    part: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.system} - {self.assembly} - {self.part}"
