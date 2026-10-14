"""Property-based invariants (run with pytest and Hypothesis installed)."""
import unittest

try:
    from hypothesis import given, settings, strategies as st
except ImportError as exc:  # Keep standard-library test discovery usable without dev extras.
    raise unittest.SkipTest("Install requirements-dev.txt to run property-based tests") from exc

from scheduler.engine import generate_timetable, validate_assignments
from scheduler.models import parse_problem


@given(session_count=st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None)
def test_unique_resources_allow_a_valid_single_slot_schedule(session_count: int) -> None:
    raw = {
        "days": ["Monday"],
        "slots": ["09:00"],
        "rooms": [f"R{i}" for i in range(session_count)],
        "sessions": [
            {"subject": f"S{i}", "section": f"S{i}", "faculty": f"F{i}"}
            for i in range(session_count)
        ],
    }
    result = generate_timetable(parse_problem(raw))
    assert result.success
    assert len(result.assignments) == session_count
    assert validate_assignments(result.assignments) == []


def test_preferred_day_is_soft_when_another_day_is_available() -> None:
    raw = {
        "days": ["Monday", "Tuesday"],
        "slots": ["09:00"],
        "rooms": ["R101", "R102"],
        "sessions": [
            {"subject": "Preferred", "section": "S1", "faculty": "Shared",
             "preferred_days": ["Monday"]},
            {"subject": "Other", "section": "S2", "faculty": "Shared"},
        ],
    }
    result = generate_timetable(parse_problem(raw))
    assert result.success
    preferred = next(row for row in result.assignments if row["subject"] == "Preferred")
    assert preferred["day"] == "Monday"
    assert validate_assignments(result.assignments) == []
