"""
This module loads a Bill of Materials from a csv file.
"""

from csv import DictReader
from dataclasses import dataclass
from pathlib import Path
from tkinter.filedialog import askopenfilename
from typing import Optional

from uploader.data import (
    Cursor,
    RowData,
    ValidationErrorData,
    _determine_fsuk_system,
    validate_data,
)

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


@dataclass
class ValidationError(ImportError):
    """Raised if the file contains invalid data."""

    errors: list[ValidationErrorData]

    def __str__(self) -> str:
        error_messages = "\n\t".join([str(error) for error in self.errors])
        return f"{len(self.errors)} error(s) found in '{self.filepath}':\n\t{error_messages}"


def load_data(
    filepath: Optional[Path] = None, *, delimiter: str = "|", skip_rows: int = 0
) -> tuple[list[RowData], Cursor]:

    if filepath is None:
        filepath = select_file()

    print(f"Loading data from '{filepath}'...")
    data, cursor = load_data_from_file(
        filepath, delimiter=delimiter, skip_rows=skip_rows
    )
    print(f"Loaded {len(data)} rows of data.\n")

    print("Validating data...")
    errors = validate_data(data)
    if len(errors) > 0:
        raise ValidationError(filepath, errors)
    print("Successfully validated data.\n")

    return data, cursor


def select_file() -> Path:
    title_text = "Select a Bill of Materials to upload"
    filepath = askopenfilename(title=title_text, filetypes=VALID_FORMATS)
    if filepath == "":
        raise NoFileSelectedError(Path(""))
    return Path(filepath)


def load_data_from_file(
    filepath: Path, delimiter: str = "|", skip_rows: int = 0
) -> tuple[list[RowData], Cursor]:

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
                if row["system"]:
                    cursor.current_system = _determine_fsuk_system(
                        row["system"]
                    )
                if row["assembly"]:
                    cursor.current_assembly = row["assembly"]
                if row["part"]:
                    cursor.current_part = row["part"]
                continue
            try:
                if not row["quantity"]:
                    row["quantity"] = 0
                if not row["cost"]:
                    row["cost"] = "NaN"
                if not row["carbon_footprint"]:
                    row["carbon_footprint"] = "NaN"

                data.append(
                    RowData(
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
                )
            except Exception as e:
                raise RowError(filepath, row=str(row), error=e)

    return data, cursor
