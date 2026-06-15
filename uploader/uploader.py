"""
This module uploads a Bill of Materials to the FSUK website.
"""

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Optional

from rich import print, progress

from uploader.data import Cursor, RowData, RowType
from uploader.webinterface import WebInterface

logger = logging.getLogger("uploader.uploader")


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


def upload_bill_of_materials(
    bom: list[RowData],
    username: str,
    password: str,
    initial_cursor: Optional[Cursor] = None,
    base_revision: int = 1,
    snapshot_label: str = "Bill of Materials",
) -> None:
    """Upload a Bill of Materials to the FSUK website."""

    logger.info("Running FSUK Bill of Materials Uploader")

    web_interface = WebInterface()
    web_interface.log_in_to_account(username, password)

    # Create new snapshot
    label = f"{snapshot_label} ({dt.datetime.now().strftime('%d %b %y %H:%M')})"
    web_interface.create_snapshot(base_revision, label)

    # Upload data
    cursor = initial_cursor if initial_cursor is not None else Cursor()
    for i, row in progress.track(
        enumerate(bom),
        description="Uploading Bill of Materials...",
        total=len(bom),
    ):
        logger.info(f"{i}/{len(bom)} Uploading {row.row_type.lower()} '{row}'")
        match row.row_type:
            case RowType.PART:
                _upload_part(web_interface, row, cursor, True)
            case RowType.STEP:
                _upload_step(web_interface, row, cursor, True)

        cursor = _update_cursor(cursor, row)

    logger.info("Bill of materials uploaded successfully!")


def _update_cursor(cursor: Cursor, row: RowData) -> Cursor:
    """Update the position of the cursor."""
    match row.row_type:
        case RowType.SYSTEM:
            cursor.system = row.fsuk_system
        case RowType.ASSEMBLY:
            cursor.assembly = row.assembly.strip()
        case RowType.PART:
            cursor.part = row.part.strip()
        case _:
            return cursor
    logger.debug(f"Cursor position set to {cursor}")
    return cursor


def _upload_part(
    web_interface: WebInterface,
    data: RowData,
    cursor: Cursor,
    upload_cost: bool,
) -> None:
    """Upload a part to the FSUK website."""
    if cursor.system is None:
        raise NoParentSystemError(data)
    if cursor.assembly is None:
        raise NoParentAssemblyError(data)
    try:
        web_interface.upload_part(
            data,
            system=cursor.system,
            assembly=cursor.assembly,
            upload_cost=upload_cost,
        )
    except Exception as e:
        print(e)
        print(f"Error: Unable to upload part '{data}'")


def _upload_step(
    web_interface: WebInterface,
    data: RowData,
    cursor: Cursor,
    upload_cost: bool,
) -> None:
    """Upload a step to the FSUK website."""
    if cursor.part is None:
        raise NoParentPartError(data)

    part_found = web_interface.select_part(cursor.part)
    if not part_found:
        raise CannotLocateParentPartError(data, parent=cursor.part)

    web_interface.upload_step(data, upload_cost=upload_cost)
