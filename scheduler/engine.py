"""Constraint-based timetable search with greedy ordering and branch-and-bound.

Preferred days are soft preferences. The solver searches for a complete feasible
schedule that maximizes the number of preferred-day matches. Failed states are
memoized; forward checking prunes branches with no legal placement for a
remaining session. The worst-case search remains exponential.
"""
from dataclasses import asdict, dataclass
from collections import Counter
from time import perf_counter
from typing import Optional

from .models import ClassSession, Problem


@dataclass(frozen=True)
class Assignment:
    day: str
    slot: str
    subject: str
    section: str
    faculty: str
    room: str


@dataclass
class ScheduleResult:
    success: bool
    assignments: list[dict]
    total_classes: int
    nodes: int
    elapsed_ms: float
    score: int
    violations: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _conflicts(session: ClassSession, day: str, slot: str, room: str,
               placed: list[tuple[int, Assignment]]) -> bool:
    """Pure predicate: check faculty, group, and room occupancy at a time."""
    return any(
        assignment.day == day and assignment.slot == slot and
        (assignment.faculty == session.faculty or
         assignment.section == session.section or assignment.room == room)
        for _, assignment in placed
    )


def _candidate_slots(problem: Problem) -> list[list[tuple[str, str, str]]]:
    """Return legal availability placements; preferences only affect ordering."""
    return [
        [
            (day, slot, room)
            for day in problem.days
            if (session.fixed_day is None or day == session.fixed_day)
            and (not session.available_days or day in session.available_days)
            for slot in problem.slots
            if (session.fixed_slot is None or slot == session.fixed_slot)
            and (not session.available_slots or slot in session.available_slots)
            for room in problem.rooms
            if (session.fixed_room is None or room == session.fixed_room)
            and (not session.available_rooms or room in session.available_rooms)
        ]
        for session in problem.sessions
    ]


def validate_assignments(assignments: list[dict]) -> list[str]:
    """Validate every pair using divide-and-conquer, independent of the solver.

    Each recursive call validates its left half, right half, and cross-half pairs.
    This makes the divide-and-conquer structure explicit for teaching; it remains
    O(n^2) time and is not claimed to outperform a straightforward pairwise loop.
    """
    def validate_range(start: int, end: int) -> list[str]:
        if end - start <= 1:
            return []
        middle = (start + end) // 2
        issues = validate_range(start, middle) + validate_range(middle, end)
        for left_index in range(start, middle):
            first = assignments[left_index]
            for right_index in range(middle, end):
                second = assignments[right_index]
                if first["day"] != second["day"] or first["slot"] != second["slot"]:
                    continue
                for key in ("faculty", "section", "room"):
                    if first[key] == second[key]:
                        issues.append(
                            f"{key} conflict: {first[key]} at "
                            f"{first['day']} {first['slot']}"
                        )
        return issues

    return validate_range(0, len(assignments))


def score_schedule(assignments: list[Assignment], preferred_day_bonus: int = 0) -> int:
    """Score a schedule: one point per placed class plus its preference bonus."""
    return len(assignments) + preferred_day_bonus


def explain_infeasibility(problem: Problem) -> list[str]:
    """Report necessary-capacity violations before suggesting broader remedies."""
    period_capacity = len(problem.days) * len(problem.slots)
    total_capacity = period_capacity * len(problem.rooms)
    explanations: list[str] = []

    if len(problem.sessions) > total_capacity:
        explanations.append(
            f"There are {len(problem.sessions)} classes but only {total_capacity} "
            "room-period placements."
        )

    for resource_name in ("faculty", "section"):
        counts = Counter(getattr(session, resource_name) for session in problem.sessions)
        for resource, count in sorted(counts.items()):
            if count > period_capacity:
                label = "Faculty" if resource_name == "faculty" else "Section"
                explanations.append(
                    f"{label} '{resource}' has {count} classes but only "
                    f"{period_capacity} distinct day/periods, so those classes cannot "
                    "all be scheduled without a clash."
                )

    if not explanations:
        explanations.append(
            "The search could not satisfy all faculty, section, and room "
            "constraints. Add days, periods, or rooms, or review the shared resources "
            "across classes."
        )
    return explanations


def generate_timetable(problem: Problem) -> ScheduleResult:
    """Find a complete valid schedule, maximizing soft preferred-day matches."""
    start = perf_counter()
    sessions = problem.sessions
    candidates = _candidate_slots(problem)
    if not sessions or any(not options for options in candidates):
        return ScheduleResult(False, [], len(sessions), 0,
                              (perf_counter() - start) * 1000, 0,
                              ["At least one session has no candidate placement."])

    # Greedy heuristic: most constrained (highest conflict degree) first.
    def degree(index: int) -> int:
        session = sessions[index]
        return sum(
            other != index and (
                sessions[other].faculty == session.faculty or
                sessions[other].section == session.section
            ) for other in range(len(sessions))
        )

    order = sorted(range(len(sessions)),
                   key=lambda index: (len(candidates[index]), -degree(index)))
    placed: list[tuple[int, Assignment]] = []
    best: list[Assignment] = []
    best_preference_bonus = -1
    failed_states: set[tuple] = set()
    nodes = 0

    def state_key(depth: int) -> tuple:
        occupancy = tuple(sorted(
            (a.day, a.slot, a.faculty, a.section, a.room) for _, a in placed
        ))
        return depth, occupancy

    def search(depth: int, preference_bonus: int) -> Optional[bool]:
        """True=feasible subtree, False=proved infeasible, None=bound-pruned."""
        nonlocal nodes, best, best_preference_bonus
        nodes += 1
        if depth == len(order):
            if preference_bonus > best_preference_bonus:
                best = [assignment for _, assignment in placed]
                best_preference_bonus = preference_bonus
            return True

        key = state_key(depth)
        if key in failed_states:
            return False

        index = order[depth]
        session = sessions[index]
        options = sorted(
            candidates[index],
            key=lambda option: (option[0] not in session.preferred_days, option),
        )
        explored_cutoff = False
        found_feasible = False

        for day, slot, room in options:
            if _conflicts(session, day, slot, room, placed):
                continue
            assignment = Assignment(day, slot, session.subject,
                                    session.section, session.faculty, room)
            placed.append((index, assignment))
            gained = int(bool(session.preferred_days) and day in session.preferred_days)
            next_bonus = preference_bonus + gained

            # Safe optimistic bound: every remaining preferred session could match.
            remaining = order[depth + 1:]
            upper_bound = next_bonus + sum(
                bool(sessions[remaining_index].preferred_days)
                for remaining_index in remaining
            )
            if best_preference_bonus >= 0 and upper_bound <= best_preference_bonus:
                explored_cutoff = True
                placed.pop()
                continue

            # Forward checking: every remaining session must retain a legal option.
            possible = all(
                any(not _conflicts(sessions[remaining_index], d, t, r, placed)
                    for d, t, r in candidates[remaining_index])
                for remaining_index in remaining
            )
            if possible:
                child_result = search(depth + 1, next_bonus)
                if child_result is True:
                    found_feasible = True
                elif child_result is None:
                    explored_cutoff = True
            placed.pop()

        if found_feasible:
            return True
        if explored_cutoff:
            return None
        failed_states.add(key)
        return False

    search(0, 0)
    rows = [asdict(assignment) for assignment in
            sorted(best, key=lambda item: (problem.days.index(item.day),
                                           problem.slots.index(item.slot), item.room))]
    issues = validate_assignments(rows)
    return ScheduleResult(
        success=bool(best) and len(best) == len(sessions),
        assignments=rows,
        total_classes=len(sessions),
        nodes=nodes,
        elapsed_ms=(perf_counter() - start) * 1000,
        score=score_schedule(best, best_preference_bonus) if best else 0,
        violations=issues,
    )


def demo_data() -> dict:
    """Small sample problem used by the web page and tests."""
    return {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "slots": ["09:00", "10:00", "11:00", "12:00"],
        "rooms": ["R101", "R102", "Lab1"],
        "sessions": [
            {"subject": "Python Programming", "section": "BCA-1A", "faculty": "Dr Rao",
             "preferred_days": ["Monday", "Wednesday"]},
            {"subject": "Mathematics", "section": "BCA-1A", "faculty": "Prof Das"},
            {"subject": "Database Systems", "section": "BCA-1A", "faculty": "Dr Iyer"},
            {"subject": "Python Lab", "section": "BCA-1B", "faculty": "Dr Rao"},
            {"subject": "Networks", "section": "BCA-1B", "faculty": "Prof Das"},
            {"subject": "Statistics", "section": "BCA-2A", "faculty": "Dr Iyer"},
            {"subject": "Algorithms", "section": "BCA-2A", "faculty": "Dr Rao"},
            {"subject": "Web Development", "section": "BCA-2A", "faculty": "Prof Das"},
        ],
    }
