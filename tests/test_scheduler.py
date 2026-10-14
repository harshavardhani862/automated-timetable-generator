import unittest
from scheduler.engine import generate_timetable, validate_assignments, demo_data
from scheduler.models import parse_problem

class SchedulerTests(unittest.TestCase):
    def test_demo_is_feasible(self):
        result = generate_timetable(parse_problem(demo_data()))
        self.assertTrue(result.success)
        self.assertEqual(len(result.assignments), result.total_classes)
        self.assertEqual(validate_assignments(result.assignments), [])

    def test_detects_conflict(self):
        rows = [
            {"day":"Mon","slot":"9","faculty":"A","section":"S1","room":"R1"},
            {"day":"Mon","slot":"9","faculty":"A","section":"S2","room":"R2"},
        ]
        self.assertTrue(any("faculty conflict" in x for x in validate_assignments(rows)))

    def test_impossible_problem_returns_failure(self):
        data = {"days":["Mon"],"slots":["9"],"rooms":["R1"],
                "sessions":[{"subject":"X","section":"S1","faculty":"A"},
                            {"subject":"Y","section":"S2","faculty":"A"}]}
        result = generate_timetable(parse_problem(data))
        self.assertFalse(result.success)


    def test_room_conflict_is_infeasible(self):
        data = {"days": ["Mon"], "slots": ["9"], "rooms": ["R1"],
                "sessions": [{"subject": "X", "section": "S1", "faculty": "A"},
                             {"subject": "Y", "section": "S2", "faculty": "B"}]}
        result = generate_timetable(parse_problem(data))
        self.assertFalse(result.success)
        self.assertEqual(result.assignments, [])

    def test_group_conflict_is_infeasible(self):
        data = {"days": ["Mon"], "slots": ["9"], "rooms": ["R1", "R2"],
                "sessions": [{"subject": "X", "section": "S1", "faculty": "A"},
                             {"subject": "Y", "section": "S1", "faculty": "B"}]}
        result = generate_timetable(parse_problem(data))
        self.assertFalse(result.success)

    def test_preferred_day_is_soft(self):
        data = {"days": ["Mon", "Tue"], "slots": ["9"], "rooms": ["R1", "R2"],
                "sessions": [{"subject": "Preferred", "section": "S1", "faculty": "A",
                              "preferred_days": ["Mon"]},
                             {"subject": "Other", "section": "S2", "faculty": "A"}]}
        result = generate_timetable(parse_problem(data))
        self.assertTrue(result.success)
        self.assertEqual(len(result.assignments), 2)
        self.assertEqual(validate_assignments(result.assignments), [])

    def test_session_availability_restricts_day_slot_and_room(self):
        data = {
            "days": ["Mon", "Tue"],
            "slots": ["9", "10"],
            "rooms": ["R1", "R2"],
            "sessions": [{
                "subject": "Lab",
                "section": "S1",
                "faculty": "A",
                "available_days": ["Tue"],
                "available_slots": ["10"],
                "available_rooms": ["R2"],
            }],
        }
        result = generate_timetable(parse_problem(data))
        self.assertTrue(result.success)
        assignment = result.assignments[0]
        self.assertEqual((assignment["day"], assignment["slot"], assignment["room"]),
                         ("Tue", "10", "R2"))

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            parse_problem({"days":[],"slots":["9"],"rooms":["R1"],"sessions":[]})

    def test_fixed_json_day_slot_and_room_are_preserved(self):
        data = {
            "days": ["Monday", "Tuesday"],
            "slots": [1, 2, 3],
            "rooms": ["R1", "R2"],
            "sessions": [
                {"day": "Tuesday", "slot": 3, "subject": "Networks",
                 "section": "S1", "faculty": "TBD", "room": "R2"},
            ],
        }
        result = generate_timetable(parse_problem(data))
        self.assertTrue(result.success)
        self.assertEqual(len(result.assignments), 1)
        row = result.assignments[0]
        self.assertEqual((row["day"], row["slot"], row["room"]),
                         ("Tuesday", "3", "R2"))

    def test_fixed_slot_with_unspecified_room_keeps_day_and_slot(self):
        data = {
            "days": ["Monday", "Saturday"],
            "slots": [1, 2, 3],
            "rooms": ["R1", "R2"],
            "sessions": [
                {"day": "Saturday", "slot": 2, "subject": "Lab",
                 "section": "S1", "faculty": "TBD", "room": None},
            ],
        }
        result = generate_timetable(parse_problem(data))
        self.assertTrue(result.success)
        row = result.assignments[0]
        self.assertEqual((row["day"], row["slot"]), ("Saturday", "2"))
        self.assertIn(row["room"], ["R1", "R2"])

if __name__ == "__main__":
    unittest.main()
