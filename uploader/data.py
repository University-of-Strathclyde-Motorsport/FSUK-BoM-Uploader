"""
This module contains data structures and validation functions for Bill of Materials data.
"""

from dataclasses import InitVar, dataclass, field
from enum import StrEnum
from typing import NamedTuple, Optional

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

    def check_for_errors(self) -> Optional[str]:

        message: Optional[str] = None

        if self.row_type == RowType.SYSTEM:
            if self.fsuk_system not in FSUKSystems:
                message = (
                    f"Invalid system {self.fsuk_system}; "
                    f"must be one of {list(map(str, FSUKSystems))}"
                )

        elif self.row_type == RowType.ASSEMBLY:
            # TODO: assembly validation
            message = None

        elif self.row_type == RowType.PART:
            if self.make_or_buy not in VALID_MAKE_OR_BUY:
                message = (
                    f"Invalid make_or_buy '{self.make_or_buy}'; "
                    f"must be one of {VALID_MAKE_OR_BUY}"
                )
            elif self.quantity < 1:
                message = (
                    f"Invalid quantity '{self.quantity}'; "
                    "must be greater than 0"
                )
            elif self.quantity > MAXIMUM_QUANTITY:
                message = (
                    f"Invalid quantity '{self.quantity}'; "
                    f"must not be greater than {MAXIMUM_QUANTITY}"
                    "(FSUK site limit)"
                )
            elif self.cost < 0:
                message = f"Invalid cost '{self.cost}'; must not be negative"
            elif self.carbon_footprint < 0:
                message = (
                    f"Invalid carbon_footprint "
                    f"'{self.carbon_footprint}'; must not be negative"
                )

        elif self.row_type == RowType.STEP:
            if self.step_type not in VALID_STEP_TYPES:
                message = (
                    f"Invalid step_type '{self.step_type}'; "
                    f"must be one of {VALID_STEP_TYPES}"
                )

        else:
            message = f"Invalid row: {self.__repr__}"

        return message


class ValidationErrorData(NamedTuple):
    """Debug information about a validation error."""

    row: int
    message: str

    def __str__(self) -> str:
        return f"Row {self.row}: {self.message}"


def validate_data(data: list[RowData]) -> list[ValidationErrorData]:
    """Validate a list of rows, and return the number of errors found."""

    errors: list[ValidationErrorData] = []

    for index, row in enumerate(data):
        error_message = row.check_for_errors()
        if error_message is not None:
            error = ValidationErrorData(row=index + 1, message=error_message)
            errors.append(error)
            print(error)

    return errors


@dataclass
class Cursor(object):
    """Dataclass holding information about where to upload rows."""

    current_system: Optional[FSUKSystems] = None
    current_assembly: Optional[str] = None
    current_part: Optional[str] = None
