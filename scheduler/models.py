"""Validated input models for the timetable application."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClassSession:
    subject: str
    section: str
    faculty: str
    duration: int = 1
    preferred_days: tuple[str, ...] = ()
    available_days: tuple[str, ...] = ()
    available_slots: tuple[str, ...] = ()
    available_rooms: tuple[str, ...] = ()
    # Optional hard constraints for JSON that already contains a timetable.
    fixed_day: str | None = None
    fixed_slot: str | None = None
    fixed_room: str | None = None


@dataclass(frozen=True)
class Problem:
    days: tuple[str, ...]
    slots: tuple[str, ...]
    rooms: tuple[str, ...]
    sessions: tuple[ClassSession, ...]


def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"'{label}' must be a list.")
    return tuple(str(item).strip() for item in value if item is not None and str(item).strip())


def parse_problem(raw: dict[str, Any]) -> Problem:
    if not isinstance(raw, dict):
        raise ValueError("The scheduling input must be a JSON object.")

    required = ("days", "slots", "rooms", "sessions")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError("Missing required keys: " + ", ".join(missing))
    if not isinstance(raw["sessions"], list):
        raise ValueError("'sessions' must be a list of class objects.")

    days = _string_tuple(raw["days"], "days")
    slots = _string_tuple(raw["slots"], "slots")
    rooms = _string_tuple(raw["rooms"], "rooms")
    if not days or not slots or not rooms:
        raise ValueError("Days, slots, and rooms must each contain at least one item.")
    if len(set(days)) != len(days) or len(set(slots)) != len(slots) or len(set(rooms)) != len(rooms):
        raise ValueError("Days, slots, and rooms must not contain duplicates.")

    sessions: list[ClassSession] = []
    for i, item in enumerate(raw["sessions"]):
        if not isinstance(item, dict):
            raise ValueError(f"Session {i + 1} must be a JSON object.")
        for key in ("subject", "section", "faculty"):
            if item.get(key) is None or not str(item.get(key, "")).strip():
                raise ValueError(f"Session {i + 1}: '{key}' is required.")

        try:
            duration = int(item.get("duration", 1))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Session {i + 1}: duration must be an integer.") from exc
        if duration != 1:
            raise ValueError("This prototype supports one-slot sessions only (duration must be 1).")

        preferred = _string_tuple(item.get("preferred_days", []), "preferred_days")
        available_days = _string_tuple(item.get("available_days", []), "available_days")
        available_slots = _string_tuple(item.get("available_slots", []), "available_slots")
        available_rooms = _string_tuple(item.get("available_rooms", []), "available_rooms")

        fixed_day = str(item["day"]).strip() if item.get("day") is not None else None
        fixed_slot = str(item["slot"]).strip() if item.get("slot") is not None else None
        fixed_room = str(item["room"]).strip() if item.get("room") is not None else None
        fixed_day = fixed_day or None
        fixed_slot = fixed_slot or None
        fixed_room = fixed_room or None

        for label, values, allowed in (
            ("preferred days", preferred, days),
            ("available days", available_days, days),
            ("available slots", available_slots, slots),
            ("available rooms", available_rooms, rooms),
        ):
            unknown_values = set(values) - set(allowed)
            if unknown_values:
                raise ValueError(f"Session {i + 1} has unknown {label}: {sorted(unknown_values)}")

        if fixed_day and fixed_day not in days:
            raise ValueError(f"Session {i + 1} has unknown fixed day: {fixed_day}")
        if fixed_slot and fixed_slot not in slots:
            raise ValueError(f"Session {i + 1} has unknown fixed slot: {fixed_slot}")
        if fixed_room and fixed_room not in rooms:
            raise ValueError(f"Session {i + 1} has unknown fixed room: {fixed_room}")

        # Fixed timetable values take precedence over availability restrictions.
        if fixed_day and available_days and fixed_day not in available_days:
            raise ValueError(f"Session {i + 1}: fixed day conflicts with available_days.")
        if fixed_slot and available_slots and fixed_slot not in available_slots:
            raise ValueError(f"Session {i + 1}: fixed slot conflicts with available_slots.")
        if fixed_room and available_rooms and fixed_room not in available_rooms:
            raise ValueError(f"Session {i + 1}: fixed room conflicts with available_rooms.")

        sessions.append(ClassSession(
            subject=str(item["subject"]).strip(),
            section=str(item["section"]).strip(),
            faculty=str(item["faculty"]).strip(),
            duration=duration,
            preferred_days=preferred,
            available_days=available_days,
            available_slots=available_slots,
            available_rooms=available_rooms,
            fixed_day=fixed_day,
            fixed_slot=fixed_slot,
            fixed_room=fixed_room,
        ))

    if not sessions:
        raise ValueError("Add at least one session.")
    return Problem(days, slots, rooms, tuple(sessions))
