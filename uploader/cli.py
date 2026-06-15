"""
This module provides a command-line interface for uploading a Bill of Materials.
"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.logging import RichHandler

from uploader.importer import load_data
from uploader.uploader import upload_bill_of_materials
from uploader.validator import validate_bill_of_materials

app = typer.Typer()

logger = logging.getLogger("uploader")
formatter = logging.Formatter("%(message)s")
handler = RichHandler(show_time=False, show_path=False)
handler.setFormatter(formatter)
logger.addHandler(handler)

webdriver_logger = logging.getLogger("uploader.webdriver")


@app.command()
def upload(
    filepath: Optional[Path] = typer.Option(
        None,
        "--input-file",
        "-f",
        help="Path to the Bill of Materials. If not provided, a file selection dialog will open.",
    ),
    delimiter: str = typer.Option(
        "|", "--delimiter", "-d", help="Delimiter for CSV file."
    ),
    skip_rows: int = typer.Option(
        0, "--skiprows", "-s", help="Rows of CSV to skip"
    ),
    username: str = typer.Option(..., "--username", "-u", prompt="Username"),
    password: str = typer.Option(
        ..., "--password", "-p", prompt="Password", hide_input=True
    ),
    base_revision: int = typer.Option(
        1, "--baserevision", "-b", help="Bill of Materials revision to clone"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show more detailed console logs"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Show highly detailed debug information"
    ),
) -> None:
    """Upload a Bill of Materials to the FSUK website."""

    logger.setLevel(logging.DEBUG if verbose or debug else logging.INFO)
    webdriver_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    bom, cursor = load_data(filepath, delimiter=delimiter, skip_rows=skip_rows)
    validate_bill_of_materials(bom)
    upload_bill_of_materials(
        bom,
        username,
        password,
        initial_cursor=cursor,
        base_revision=base_revision,
    )
