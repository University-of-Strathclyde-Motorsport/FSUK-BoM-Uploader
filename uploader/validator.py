"""
This module checks a Bill of Materials for errors before it is uploaded.
"""

import logging
import math
from dataclasses import dataclass
from typing import Callable

from uploader.data import FSUKSystems, RowData, RowType
from uploader.importer import VALID_FORMATS

logger = logging.getLogger("uploader.validator")

MAXIMUM_QUANTITY = 999
PART_NAME_CHARACTER_LIMIT = 50
FORBIDDEN_CHARACTERS = "<>"
VALID_MAKE_OR_BUY = ["Make", "Buy"]
VALID_STEP_TYPES = ["Material", "Process", "Fasteners", "Tooling"]

type RowValidationFunction = Callable[[RowData], None]


@dataclass
class ValidationError(Exception):
    """Raised if the file contains invalid data."""

    error_count: int

    def __str__(self) -> str:
        return f"Found {self.error_count} errors in Bill of Materials."


def system_is_valid(row: RowData) -> None:
    """Check that systems are valid."""
    if row.row_type == RowType.SYSTEM:
        assert row.fsuk_system in FSUKSystems, (
            f"Invalid system '{row.fsuk_system}'"
        )


def part_name_under_character_limit(row: RowData) -> None:
    """Check that part names are below the FSUK character limit."""
    if row.row_type == RowType.PART:
        assert len(row.part) <= PART_NAME_CHARACTER_LIMIT, (
            f"Part '{row.part}' has {len(row.part)} characters, more than the allowed {PART_NAME_CHARACTER_LIMIT}"
        )


def quantity_is_positive(row: RowData) -> None:
    """Check that quantities are positive."""
    if row.requires_quantity():
        assert row.quantity >= 1, (
            f"Invalid quantity {row.quantity}; must be positive"
        )


def quantity_below_maximum(row: RowData) -> None:
    """Check that quantity is below maximum."""
    if row.requires_quantity():
        assert row.quantity <= MAXIMUM_QUANTITY, (
            f"Quantity of {row.quantity} is greater than maximum allowed by FSUK ({MAXIMUM_QUANTITY})"
        )


def valid_make_or_buy(row: RowData) -> None:
    """Check that the make or buy column is valid."""
    if row.row_type == RowType.PART:
        assert row.make_or_buy in VALID_MAKE_OR_BUY, (
            f"Invalid M/B '{row.make_or_buy}'; must be one of {VALID_MAKE_OR_BUY}"
        )


def valid_step_type(row: RowData) -> None:
    """Check that the step type column is valid."""
    if row.row_type == RowType.STEP:
        assert row.step_type in VALID_FORMATS, (
            f"Invalid M/P/F/T '{row.step_type}'; must be one of {VALID_STEP_TYPES}"
        )


def cost_is_nonnegative(row: RowData) -> None:
    """Check that cost is nonnegative."""
    if row.cost:
        assert row.cost >= 0 or math.isnan(row.cost), (
            f"Invalid cost {row.cost}; must be nonnegative"
        )


def emissions_are_nonnegative(row: RowData) -> None:
    """Check that emissions are nonnegative."""
    if row.carbon_footprint:
        assert row.carbon_footprint >= 0 or math.isnan(row.carbon_footprint), (
            f"Invalid emissions {row.carbon_footprint}; must be nonnegative"
        )


def no_forbidden_characters(row: RowData) -> None:
    """Check that text inputs do not contain any forbidden characters."""

    def assert_no_forbidden_characters(text: str) -> None:
        """Return a list of forbidden characters."""
        forbidden = {char for char in text if char in FORBIDDEN_CHARACTERS}
        assert not forbidden, (
            f"'{text}' contains forbidden characters {''.join(forbidden)}"
        )

    if row.part:
        assert_no_forbidden_characters(row.part)

    if row.subtype:
        assert_no_forbidden_characters(row.subtype)

    if row.comment:
        assert_no_forbidden_characters(row.comment)


VALIDATION_FUNCTIONS: list[RowValidationFunction] = [
    system_is_valid,
    part_name_under_character_limit,
    quantity_is_positive,
    quantity_below_maximum,
    valid_make_or_buy,
    cost_is_nonnegative,
    emissions_are_nonnegative,
    no_forbidden_characters,
]


def validate_bill_of_materials(data: list[RowData]) -> None:
    """Perform a list of checks on a Bill of Materials."""
    error_count = 0
    for i, row in enumerate(data):
        for validation_function in VALIDATION_FUNCTIONS:
            try:
                validation_function(row)
            except AssertionError as e:
                error_count += 1
                logger.warning(str(e))
    if error_count > 0:
        raise ValidationError(error_count)
        # logger.critical(f"{error_count} error(s) found in Bill of Materials.")
    else:
        logger.info("Successfully validated Bill of Materials.")
