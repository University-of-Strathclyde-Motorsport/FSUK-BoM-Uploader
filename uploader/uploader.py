"""
This module uploads a Bill of Materials to the FSUK website.
"""

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from uploader.data import RowData, RowType
from uploader.importer import load_data
from uploader.webinterface import WebInterface


@dataclass
class UploadError(Exception):
    """Base class for errors raised during the upload process."""

    row_data: RowData


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

    current_system: Optional[str] = None
    current_assembly: Optional[str] = None
    current_part: Optional[str] = None


class Uploader:
    def __init__(
        self,
        base_revision: int = 1,
        snapshot_label: str = "Bill of Materials",
        upload_cost: bool = True,
    ):

        self.base_revision = base_revision
        self.snapshot_label = snapshot_label
        self.upload_cost = upload_cost
        self.upload_bill_of_materials()

    def upload_bill_of_materials(self) -> None:

        print("\nRunning FSUK Bill of Materials Uploader\n")

        data = load_data()  # Load and validate data
        self.web_interface = create_web_interface()  # Log into FSUK account

        # Create new snapshot
        timestamp = dt.datetime.now().strftime("%d %b %y %H:%M")
        label = f"{self.snapshot_label} ({timestamp})"
        print(
            f"Creating new snapshot '{label}' "
            f"from base revision {self.base_revision}..."
        )
        self.web_interface.create_snapshot(self.base_revision, label)

        # Upload data
        print("Uploading bill of materials...")
        self.upload_data(data)
        print("Bill of materials uploaded successfully.")

    def upload_data(self, data: list[RowData]) -> None:

        cursor = Cursor()

        for index, row in enumerate(data):
            current_row = f"({index + 1}/{len(data)})"
            row_type = row.row_type.lower()
            print(f"{current_row} Uploading {row_type} '{row}'...")

            match row.row_type:
                case RowType.SYSTEM:
                    cursor.current_system = row.system
                case RowType.ASSEMBLY:
                    cursor.current_assembly = row.assembly
                case RowType.PART:
                    cursor.current_part = self.upload_part(row, cursor)
                case RowType.STEP:
                    self.upload_step(row, cursor)
                case _:
                    continue

    def upload_part(self, data: RowData, cursor: Cursor) -> Optional[str]:
        if cursor.current_system is None:
            raise NoParentSystemError(data)
        if cursor.current_assembly is None:
            raise NoParentAssemblyError(data)
        try:
            self.web_interface.upload_part(
                data,
                system=cursor.current_system,
                assembly=cursor.current_assembly,
                upload_cost=self.upload_cost,
            )
            return data.part
        except Exception as e:
            print(e)
            print(f"Error: Unable to upload part '{data}'")
            return None

    def upload_step(self, data: RowData, cursor: Cursor) -> None:
        if cursor.current_part is None:
            raise NoParentPartError(data)

        part_found = self.web_interface.select_part(cursor.current_part)
        if not part_found:
            raise CannotLocateParentPartError(data, parent=cursor.current_part)

        self.web_interface.upload_step(data, upload_cost=self.upload_cost)


def create_web_interface() -> WebInterface:
    while True:
        username, password = get_username_and_password()
        print("Attempting to log into FSUK account...")
        try:
            web_interface = WebInterface()
            web_interface.log_in_to_account(username, password)
            print("Login successful.\n")
            return web_interface
        except Exception as e:
            print(e)
            print("Login failed: invalid credentials.")
            try_again = input("Would you like to try again? (yes/no)")
            if try_again.lower() not in ["yes", "y"]:
                raise Exception("User exited programme.")


def get_username_and_password() -> tuple[str, str]:
    print("Please enter your FSUK credentials:")
    username = input("Username: ")
    password = input("Password: ")
    return username, password
