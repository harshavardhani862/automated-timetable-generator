"""CSV and XLSX import for institution timetable data."""
from __future__ import annotations

import csv
import io
import itertools
import re
from typing import Any, BinaryIO
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .models import Problem, parse_problem

MAX_IMPORT_ROWS = 250
REQUIRED_COLUMNS = {"subject", "section", "faculty", "rooms"}


def _split_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in re.split(r"[;|]", str(value)) if part.strip())


def _normalise_header(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[\s-]+", "_", str(value).strip().lower())


def _read_rows(stream: BinaryIO, filename: str) -> list[list[Any]]:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content = stream.read()
    if not content:
        raise ValueError("The uploaded file is empty.")

    if extension == "csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV files must use UTF-8 encoding.") from exc
        try:
            return list(
                itertools.islice(
                    csv.reader(io.StringIO(text, newline="")), MAX_IMPORT_ROWS + 2
                )
            )
        except csv.Error as exc:
            raise ValueError("The CSV file contains malformed rows.") from exc
    if extension == "xlsx":
        try:
            workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except (
            BadZipFile,
            InvalidFileException,
            OSError,
            ParseError,
            ValueError,
        ) as exc:
            raise ValueError("The Excel file could not be opened. Upload a valid .xlsx file.") from exc
        try:
            worksheet = workbook["Sessions"] if "Sessions" in workbook.sheetnames else workbook.active
            return [
                list(row)
                for row in itertools.islice(
                    worksheet.iter_rows(values_only=True), MAX_IMPORT_ROWS + 2
                )
            ]
        except (BadZipFile, OSError, ParseError, ValueError) as exc:
            raise ValueError(
                "The Excel file could not be read. Check that the .xlsx workbook is valid."
            ) from exc
        finally:
            workbook.close()
    raise ValueError("Upload a .csv or .xlsx file.")


def parse_schedule_file(
    stream: BinaryIO,
    filename: str,
    days: tuple[str, ...],
    slots: tuple[str, ...],
) -> Problem:
    """Parse a session sheet and validate its rooms and availability against the form."""
    rows = _read_rows(stream, filename)
    if not rows:
        raise ValueError("The uploaded file must include a header row.")

    headers = [_normalise_header(value) for value in rows[0]]
    populated_headers = [header for header in headers if header]
    if len(set(populated_headers)) != len(populated_headers):
        raise ValueError("The uploaded file contains duplicate column names.")
    missing = sorted(REQUIRED_COLUMNS - set(headers))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    indexes = {name: index for index, name in enumerate(headers) if name}
    sessions: list[dict[str, Any]] = []
    all_rooms: set[str] = set()
    for row_number, row in enumerate(rows[1:], start=2):
        if not any(value is not None and str(value).strip() for value in row):
            continue
        if len(sessions) >= MAX_IMPORT_ROWS:
            raise ValueError(f"Import is limited to {MAX_IMPORT_ROWS} class rows.")
        record = {name: row[index] if index < len(row) else None
                  for name, index in indexes.items()}
        room_options = _split_values(record.get("rooms"))
        if not room_options:
            raise ValueError(f"Row {row_number}: add at least one room in the 'rooms' column.")
        all_rooms.update(room_options)
        sessions.append({
            "subject": str(record.get("subject") or "").strip(),
            "section": str(record.get("section") or "").strip(),
            "faculty": str(record.get("faculty") or "").strip(),
            "available_rooms": room_options,
            "available_days": _split_values(record.get("available_days")),
            "available_slots": _split_values(record.get("available_slots")),
            "preferred_days": _split_values(record.get("preferred_days")),
        })
    if not sessions:
        raise ValueError("The uploaded file contains no class rows.")

    try:
        return parse_problem({
            "days": days,
            "slots": slots,
            "rooms": tuple(sorted(all_rooms)),
            "sessions": sessions,
        })
    except ValueError as exc:
        match = re.match(r"Session (\d+)(.*)", str(exc))
        if match:
            raise ValueError(f"Row {int(match.group(1)) + 1}{match.group(2)}") from exc
        raise
