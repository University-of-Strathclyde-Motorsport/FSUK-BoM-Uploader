from dataclasses import dataclass, field
from enum import StrEnum


VALID_MAKE_OR_BUY = ["Make", "Buy"]
VALID_STEP_TYPES = ["Material", "Process", "Fasteners", "Tooling"]
MAXIMUM_QUANTITY = 999


class RowType(StrEnum):
    SYSTEM = "System"
    ASSEMBLY = "Assembly"
    PART = "Part"
    STEP = "Step"
    UNDEFINED = "Undefined"


class FSUKSystems(StrEnum):
    BR = "Brake System"
    FR = "Chassis and Body"
    DT = "Drivetrain"
    TS = "Engine and Tractive System"
    EL = "Grounded Low Voltage System"
    MS = "Miscellaneous"
    ST = "Steering System"
    SU = "Suspension System"
    WT = "Wheels and Tyres"


@dataclass
class RowData:
    row_type: RowType = field(init=False)
    system: str
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
    

    def __post_init__(self) -> None:
        if self.system != "":
            self.row_type = RowType.SYSTEM
        elif self.assembly != "":
            self.row_type = RowType.ASSEMBLY
        elif self.part != "":
            self.row_type = RowType.PART
        elif self.step_type != "":
            self.row_type = RowType.STEP
        else:
            self.row_type = RowType.UNDEFINED


    def validate(self) -> tuple[bool, str]:
        message = ""

        if self.row_type == RowType.SYSTEM:
            if self.system not in FSUKSystems:
                message = f"Invalid system {self.system}; " \
                          f"must be one of {list(map(str, FSUKSystems))}"

        elif self.row_type == RowType.ASSEMBLY:
            # TODO: assembly validation
            message = ""

        elif self.row_type == RowType.PART:
            if self.make_or_buy not in VALID_MAKE_OR_BUY:
                message = f"Invalid make_or_buy '{self.make_or_buy}'; " \
                          f"must be one of {VALID_MAKE_OR_BUY}"
            elif self.quantity < 1:
                message = f"Invalid quantity '{self.quantity}'; " \
                          "must be greater than 0"
            elif self.quantity > MAXIMUM_QUANTITY:
                message = f"Invalid quantity '{self.quantity}'; " \
                          f"must not be greater than {MAXIMUM_QUANTITY}" \
                           "(FSUK site limit)"
            elif self.cost < 0:
                message = f"Invalid cost '{self.cost}'; " \
                          "must not be negative"
            elif self.carbon_footprint < 0:
                message = f"Invalid carbon_footprint " \
                          f"'{self.carbon_footprint}'; must not be negative"

        elif self.row_type == RowType.STEP:
            if self.step_type not in VALID_STEP_TYPES:
                message = f"Invalid step_type '{self.step_type}'; " \
                          f"must be one of {VALID_STEP_TYPES}"

        else:
            message = "Invalid row"
        
        if message == "":
            return True, ""
        else:
            return False, message

        
    def get_identifier(self) -> str:
        if self.row_type == RowType.SYSTEM:
            return self.system
        elif self.row_type == RowType.ASSEMBLY:
            return self.assembly
        elif self.row_type == RowType.PART:
            return self.part
        elif self.row_type == RowType.STEP:
            return f"{self.step_type}: {self.subtype}"
        else:
            return "Invalid row"


def validate_data(data: list[RowData]) -> int:
    
    error_count = 0

    for index, row in enumerate(data):
        is_valid, message = row.validate()
        if not is_valid:
            print(f"Error (row {index + 1}): {message}")
            error_count += 1

    return error_count