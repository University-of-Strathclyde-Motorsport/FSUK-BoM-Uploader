"""
This module provides a command-line interface for uploading a Bill of Materials.
"""

from pathlib import Path
from typing import Optional

import typer

from uploader.importer import load_data
from uploader.uploader import upload_bill_of_materials

app = typer.Typer()


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
    username: str = typer.Option(..., "--username", "-u", prompt="Username"),
    password: str = typer.Option(
        ..., "--password", "-p", prompt="Password", hide_input=True
    ),
) -> None:
    """Upload a Bill of Materials to the FSUK website."""

    bom = load_data(filepath, delimiter=delimiter)
    upload_bill_of_materials(bom, username, password)
