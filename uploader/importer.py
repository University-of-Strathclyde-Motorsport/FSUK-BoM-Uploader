"""
This module loads a Bill of Materials from a csv file.
"""

import logging
from csv import DictReader
from dataclasses import dataclass
from pathlib import Path
from tkinter.filedialog import askopenfilename
from typing import Any, Optional

from uploader.data import Cursor, RowData, _determine_fsuk_system

logger = logging.getLogger("uploader.importer")

VALID_FORMATS = [("CSV", ".csv")]
REQUIRED_FIELDS = {
    "system",
    "assembly",
    "part",
    "make_or_buy",
    "step_type",
    "subtype",
    "comment",
    "quantity",
    "cost",
    "cost_comment",
    "carbon_footprint",
    "carbon_comment",
}


@dataclass
class ImportError(Exception):
    """Base class for errors raised during the import process."""

    filepath: Path


class NoFileSelectedError(ImportError):
    """Raised if no file is selected."""

    def __str__(self) -> str:
        return "No file selected."


@dataclass
class InvalidFileFormatError(ImportError):
    """Raised if the file format is invalid."""

    valid_formats: list[str]

    def __str__(self) -> str:
        return (
            f"Invalid file format '{self.filepath.suffix}'."
            f"Expected one of {self.valid_formats}."
        )


class NoDataError(ImportError):
    """Raised if the file contains no data."""

    def __str__(self) -> str:
        return f"No data found in the '{self.filepath}'."


class IncorrectColumnsError(ImportError):
    """Raised if the file does not contain the required columns."""

    def __str__(self) -> str:
        return f"Incorrect columns in '{self.filepath}'\nExpected: {REQUIRED_FIELDS}"


@dataclass
class RowError(ImportError):
    """Raised if an error occurs while importing a row."""

    row: str
    error: Exception

    def __str__(self) -> str:
        return (
            f"An error occured while loading the following row:\n{self.row}\n"
            f"Error details: {self.error}"
        )


def load_data(
    filepath: Optional[Path] = None, *, delimiter: str = "|", skip_rows: int = 0
) -> tuple[list[RowData], Cursor]:
    """Import a Bill of Materials from a CSV file."""

    if filepath is None:
        filepath = _prompt_for_file()

    logger.info(f"Loading data from '{filepath}'...")
    valid_formats = [format[1] for format in VALID_FORMATS]
    if filepath.suffix not in valid_formats:
        raise InvalidFileFormatError(filepath, valid_formats)

    with open(filepath, newline="") as file:
        reader = DictReader(file, delimiter=delimiter)

        if reader.fieldnames is None:
            raise NoDataError(filepath)

        if not REQUIRED_FIELDS.issubset(set(reader.fieldnames)):
            raise IncorrectColumnsError(filepath)

        data: list[RowData] = []
        cursor = Cursor()

        for i, row in enumerate(reader):
            if i < skip_rows:
                cursor = _update_cursor_position(cursor, row)
                continue
            try:
                data.append(_parse_row_data(row))
            except Exception as e:
                raise RowError(filepath, row=str(row), error=e)

    logger.info(f"Loaded {len(data)} rows of data.")
    if skip_rows:
        logger.info(f"Initial cursor position: {cursor}")
        logger.info(f"First row: {data[0]}")
    return data, cursor


def _prompt_for_file() -> Path:
    """Prompt the user to select a Bill of Materials file."""
    title_text = "Select a Bill of Materials to upload"
    filepath = askopenfilename(title=title_text, filetypes=VALID_FORMATS)
    if filepath == "":
        raise NoFileSelectedError(Path(""))
    return Path(filepath)


def _update_cursor_position(cursor: Cursor, row: dict[str, str]) -> Cursor:
    """Update the position of the cursor."""
    if row["system"]:
        cursor.system = _determine_fsuk_system(row["system"])
    if row["assembly"]:
        cursor.assembly = row["assembly"]
    if row["part"]:
        cursor.part = row["part"]
    return cursor


def _parse_row_data(row: dict[str, Any]) -> RowData:
    """Parse a row data dictionary into a RowData object."""
    if not row["quantity"]:
        row["quantity"] = 0
    if not row["cost"]:
        row["cost"] = "NaN"
    if not row["carbon_footprint"]:
        row["carbon_footprint"] = "NaN"

    return RowData(
        system=row["system"],
        assembly=row["assembly"],
        part=row["part"],
        make_or_buy=row["make_or_buy"],
        step_type=row["step_type"],
        subtype=row["subtype"],
        comment=row["comment"],
        quantity=int(row["quantity"]),
        cost=float(row["cost"]),
        cost_comment=row["cost_comment"],
        carbon_footprint=float(row["carbon_footprint"]),
        carbon_comment=row["carbon_comment"],
    )
