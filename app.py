"""Flask application for the CampusOS timetable workspace."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

from scheduler.engine import demo_data, explain_infeasibility, generate_timetable
from scheduler.importer import parse_schedule_file
from scheduler.models import Problem, parse_problem

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

DEFAULT_DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
DEFAULT_SLOTS = ("09:00", "10:00", "11:00", "12:00")


def _build_timetable_grid(
    days: list[str],
    slots: list[str],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group parallel room bookings by day and period."""
    bookings: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for assignment in assignments:
        key = (assignment["day"], assignment["slot"])
        bookings.setdefault(key, []).append(assignment)
    return [
        {"day": day, "cells": [bookings.get((day, slot), []) for slot in slots]}
        for day in days
    ]


def _split_form_values(value: str, label: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in value.split(",") if part.strip())
    if not values:
        raise ValueError(f"Enter at least one {label}, separated by commas.")
    if len(set(values)) != len(values):
        raise ValueError(f"Remove duplicate {label} values.")
    return values


def _dashboard(
    problem: Problem,
    problem_json: str,
    *,
    error: str | None = None,
    error_title: str | None = None,
    imported_filename: str | None = None,
    days_config: str | None = None,
    slots_config: str | None = None,
    status_message: str | None = None,
):
    result = generate_timetable(problem).to_dict()
    days = list(problem.days)
    slots = list(problem.slots)
    assignments = result["assignments"]
    return render_template(
        "index.html",
        problem_json=problem_json,
        result=result,
        days=days,
        slots=slots,
        grid=_build_timetable_grid(days, slots, assignments),
        diagnostics=(
            explain_infeasibility(problem) if not result["success"] else []
        ),
        error=error,
        error_title=error_title,
        imported_filename=imported_filename,
        days_config=days_config or ", ".join(days),
        slots_config=slots_config or ", ".join(slots),
        status_message=status_message,
        section_count=len({session.section for session in problem.sessions}),
        faculty_count=len({session.faculty for session in problem.sessions}),
        room_count=len(problem.rooms),
    )


@app.route("/", methods=["GET", "POST"])
def index():
    problem_json = json.dumps(demo_data(), indent=2)
    if request.method == "GET":
        problem = parse_problem(demo_data())
        return _dashboard(problem, problem_json, status_message="Demo schedule loaded")

    problem_json = request.form.get("problem", problem_json)
    try:
        problem = parse_problem(json.loads(problem_json))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return _dashboard(
            parse_problem(demo_data()),
            problem_json,
            error=str(exc),
            error_title="Could not read scheduling input",
        )
    return _dashboard(problem, problem_json, status_message="Schedule generated")


@app.post("/import")
def import_schedule():
    uploaded = request.files.get("file")
    days_config = request.form.get("days", "")
    slots_config = request.form.get("slots", "")
    try:
        if uploaded is None or not uploaded.filename:
            raise ValueError("Choose a .csv or .xlsx timetable file to import.")
        filename = secure_filename(uploaded.filename)
        days = _split_form_values(days_config, "days")
        slots = _split_form_values(slots_config, "periods")
        problem = parse_schedule_file(uploaded.stream, filename, days, slots)
    except (ValueError, OSError) as exc:
        return _dashboard(
            parse_problem(demo_data()),
            json.dumps(demo_data(), indent=2),
            error=str(exc),
            error_title="Spreadsheet import failed",
            days_config=days_config or ", ".join(DEFAULT_DAYS),
            slots_config=slots_config or ", ".join(DEFAULT_SLOTS),
        )
    return _dashboard(
        problem,
        json.dumps(
            {
                "days": problem.days,
                "slots": problem.slots,
                "rooms": problem.rooms,
                "sessions": [
                    {
                        "subject": session.subject,
                        "section": session.section,
                        "faculty": session.faculty,
                        "preferred_days": session.preferred_days,
                        "available_days": session.available_days,
                        "available_slots": session.available_slots,
                        "available_rooms": session.available_rooms,
                    }
                    for session in problem.sessions
                ],
            },
            indent=2,
        ),
        imported_filename=filename,
        days_config=days_config,
        slots_config=slots_config,
        status_message="Spreadsheet imported and schedule generated",
    )


@app.get("/import-template.csv")
def import_template():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "subject",
        "section",
        "faculty",
        "rooms",
        "available_days",
        "available_slots",
        "preferred_days",
    ])
    writer.writerow([
        "Algorithms",
        "CS-3A",
        "Dr Rao",
        "Room 301;Room 302",
        "Monday;Wednesday",
        "09:00;10:00",
        "Monday",
    ])
    writer.writerow([
        "Database Systems",
        "CS-3B",
        "Prof Iyer",
        "Lab 1",
        "Tuesday;Thursday",
        "11:00;12:00",
        "",
    ])
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="campusos-sessions-template.csv",
    )


@app.post("/export")
def export_csv():
    try:
        rows = json.loads(request.form["data"])
    except (KeyError, json.JSONDecodeError):
        return "Invalid export data.", 400
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return "Invalid export data.", 400
    output = io.StringIO(newline="")
    fields = ["day", "slot", "subject", "section", "faculty", "room"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _spreadsheet_safe(row.get(key, "")) for key in fields})
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="campusos-timetable.csv",
    )


def _spreadsheet_safe(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


@app.errorhandler(413)
def upload_too_large(_error):
    del _error
    return "The uploaded file is too large. Maximum size is 5 MB.", 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
