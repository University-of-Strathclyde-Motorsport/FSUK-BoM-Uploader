"""
This module uploads a Bill of Materials to the FSUK website.
"""

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from uploader.data import FSUKSystems, RowData, RowType
from uploader.webinterface import WebInterface


@dataclass
class UploadError(Exception):
    """Base class for errors raised during the upload process."""

    row_data: RowData


class InvalidCredentialsError(Exception):
    """Raised if FSUK credentials are invalid."""

    def __str__(self) -> str:
        return "Unable to log into FSUK website; invalid credentials."


class NoParentSystemError(UploadError):
    """Raised if a part is uploaded when no parent part exists."""

    def __str__(self) -> str:
        return f"Cannot upload part '{self.row_data}'; no parent system exists."


class NoParentAssemblyError(UploadError):
    """Raised if a part is uploaded when no parent assembly exists."""

    def __str__(self) -> str:
        return (
            f"Cannot upload part '{self.row_data}'; no parent assembly exists."
        )


class NoParentPartError(UploadError):
    """Raised if a step is uploaded when no parent part exists."""

    def __str__(self) -> str:
        return f"Cannot upload step '{self.row_data}'; no parent part exists."


@dataclass
class CannotLocateParentPartError(UploadError):
    """Raised if the parent part cannot be located."""

    parent: str

    def __str__(self) -> str:
        return f"Cannot upload step '{self.row_data}'; unable to locate parent part '{self.parent}'."


@dataclass
class Cursor(object):
    """Dataclass holding information about where to upload rows."""

    current_system: Optional[FSUKSystems] = None
    current_assembly: Optional[str] = None
    current_part: Optional[str] = None


def upload_bill_of_materials(
    bom: list[RowData],
    username: str,
    password: str,
    base_revision: int = 1,
    snapshot_label: str = "Bill of Materials",
) -> None:
    """Upload a Bill of Materials to the FSUK website."""

    print("\nRunning FSUK Bill of Materials Uploader\n")

    web_interface = _create_web_interface(
        username, password
    )  # Log into FSUK account

    # Create new snapshot
    timestamp = dt.datetime.now().strftime("%d %b %y %H:%M")
    label = f"{snapshot_label} ({timestamp})"
    print(
        f"Creating new snapshot '{label}' from base revision {base_revision}..."
    )
    web_interface.create_snapshot(base_revision, label)

    # Upload data
    print("Uploading bill of materials...")
    _upload_data(web_interface, bom, upload_cost=True)
    print("Bill of materials uploaded successfully.")


def _upload_data(
    web_interface: WebInterface, data: list[RowData], upload_cost: bool
) -> None:
    """Input the data to the website."""

    cursor = Cursor()

    for index, row in enumerate(data):
        current_row = f"({index + 1}/{len(data)})"
        row_type = row.row_type.lower()
        print(f"{current_row} Uploading {row_type} '{row}'...")

        match row.row_type:
            case RowType.SYSTEM:
                cursor.current_system = row.fsuk_system
            case RowType.ASSEMBLY:
                cursor.current_assembly = row.assembly
            case RowType.PART:
                cursor.current_part = _upload_part(
                    web_interface, row, cursor, upload_cost
                )
            case RowType.STEP:
                _upload_step(web_interface, row, cursor, upload_cost)
            case _:
                print(f"Skipping row due to invalid row type:\n{row}")


def _upload_part(
    web_interface: WebInterface,
    data: RowData,
    cursor: Cursor,
    upload_cost: bool,
) -> Optional[str]:
    """Upload a part to the FSUK website."""
    if cursor.current_system is None:
        raise NoParentSystemError(data)
    if cursor.current_assembly is None:
        raise NoParentAssemblyError(data)
    try:
        web_interface.upload_part(
            data,
            system=cursor.current_system,
            assembly=cursor.current_assembly,
            upload_cost=upload_cost,
        )
        return data.part
    except Exception as e:
        print(e)
        print(f"Error: Unable to upload part '{data}'")
        return None


def _upload_step(
    web_interface: WebInterface,
    data: RowData,
    cursor: Cursor,
    upload_cost: bool,
) -> None:
    """Upload a step to the FSUK website."""
    if cursor.current_part is None:
        raise NoParentPartError(data)

    part_found = web_interface.select_part(cursor.current_part)
    if not part_found:
        raise CannotLocateParentPartError(data, parent=cursor.current_part)

    web_interface.upload_step(data, upload_cost=upload_cost)


def _create_web_interface(username: str, password: str) -> WebInterface:
    """Create a WebInterface and log in to the FSUK website."""
    while True:
        print("Attempting to log into FSUK account...")
        try:
            web_interface = WebInterface()
            web_interface.log_in_to_account(username, password)
            print("Login successful.\n")
            return web_interface
        except Exception:
            raise InvalidCredentialsError()
