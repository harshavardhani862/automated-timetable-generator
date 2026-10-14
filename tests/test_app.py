"""Flask integration tests for the timetable workspace."""
from io import BytesIO
import json
import unittest

from openpyxl import Workbook

from app import _build_timetable_grid, app
from scheduler.engine import demo_data


class AppIntegrationTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_loads_sample_and_b2b_workspace(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Timetable workspace", response.data)
        self.assertIn(b"Northstar University", response.data)
        self.assertIn(b"Weekly timetable", response.data)
        self.assertIn(b"Python Programming", response.data)
        self.assertIn(b"Import &amp; generate", response.data)

    def test_json_schedule_uses_sections(self):
        response = self.client.post("/", data={"problem": json.dumps(demo_data())})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No conflicts detected", response.data)
        self.assertIn(b"8</strong> / 8 classes placed", response.data)
        self.assertIn(b"BCA-1A", response.data)
        self.assertNotIn(b"Group:", response.data)

    def test_grid_shows_empty_periods_and_parallel_room_bookings(self):
        assignments = [
            {"day": "Monday", "slot": "1", "subject": "Algorithms",
             "section": "S1", "faculty": "F1", "room": "R1"},
            {"day": "Monday", "slot": "1", "subject": "Databases",
             "section": "S2", "faculty": "F2", "room": "R2"},
        ]
        grid = _build_timetable_grid(["Monday", "Tuesday"], ["1", "2"], assignments)

        self.assertEqual(grid[0]["cells"][0], assignments)
        self.assertEqual(grid[0]["cells"][1], [])
        self.assertEqual(grid[1]["cells"], [[], []])

    def test_csv_upload_imports_session_sections_rooms_and_availability(self):
        csv_data = (
            "subject,section,faculty,rooms,available_days,available_slots,preferred_days\n"
            "Algorithms,CS-3A,Dr Rao,Room 301;Room 302,Monday,09:00,Monday\n"
            "Databases,CS-3B,Prof Iyer,Lab 1,Tuesday,10:00,\n"
        )
        response = self.client.post(
            "/import",
            data={
                "days": "Monday, Tuesday",
                "slots": "09:00, 10:00",
                "file": (BytesIO(csv_data.encode()), "sessions.csv"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"sessions.csv imported", response.data)
        self.assertIn(b"CS-3A", response.data)
        self.assertIn(b"Room 301", response.data)
        self.assertIn(b"2</strong> / 2 classes placed", response.data)

    def test_xlsx_upload_reads_sessions_worksheet(self):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Sessions"
        worksheet.append([
            "subject", "section", "faculty", "rooms", "available_days",
            "available_slots", "preferred_days",
        ])
        worksheet.append(["Networks", "IT-2B", "Dr Sen", "Lab A", "Wednesday", "11:00", ""])
        file_data = BytesIO()
        workbook.save(file_data)
        file_data.seek(0)

        response = self.client.post(
            "/import",
            data={
                "days": "Wednesday",
                "slots": "11:00",
                "file": (file_data, "sessions.xlsx"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"IT-2B", response.data)
        self.assertIn(b"Lab A", response.data)
        self.assertIn(b"1</strong> / 1 classes placed", response.data)

    def test_import_rejects_unknown_availability(self):
        csv_data = (
            "subject,section,faculty,rooms,available_days\n"
            "Algorithms,CS-3A,Dr Rao,Room 301,Sunday\n"
        )
        response = self.client.post(
            "/import",
            data={
                "days": "Monday",
                "slots": "09:00",
                "file": (BytesIO(csv_data.encode()), "sessions.csv"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"unknown available days", response.data)

    def test_import_rejects_missing_required_columns(self):
        response = self.client.post(
            "/import",
            data={
                "days": "Monday",
                "slots": "09:00",
                "file": (BytesIO(b"subject,section\nMath,S1\n"), "sessions.csv"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Missing required columns", response.data)

    def test_download_import_template(self):
        response = self.client.get("/import-template.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn(b"subject,section,faculty,rooms", response.data)

    def test_invalid_json_shows_error_without_hiding_workspace(self):
        response = self.client.post("/", data={"problem": "{invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not read scheduling input", response.data)
        self.assertIn(b"Weekly timetable", response.data)

    def test_csv_export_uses_section_header(self):
        rows = [{"day": "Monday", "slot": "09:00", "subject": "Python",
                 "section": "BCA-1A", "faculty": "Dr Rao", "room": "R101"}]
        response = self.client.post("/export", data={"data": json.dumps(rows)})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn(b"day,slot,subject,section,faculty,room", response.data)
        self.assertIn(b"Monday,09:00,Python,BCA-1A,Dr Rao,R101", response.data)

    def test_csv_export_neutralizes_spreadsheet_formulas(self):
        rows = [{"day": "Monday", "slot": "09:00", "subject": "=1+1",
                 "section": "S1", "faculty": "Dr Rao", "room": "R101"}]
        response = self.client.post("/export", data={"data": json.dumps(rows)})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Monday,09:00,'=1+1,S1,Dr Rao,R101", response.data)


if __name__ == "__main__":
    unittest.main()
