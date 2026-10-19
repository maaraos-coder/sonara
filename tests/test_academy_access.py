import unittest
from unittest.mock import patch

import academy_access


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args):
        return self

    def eq(self, field, value):
        self.rows = [row for row in self.rows if row.get(field) == value]
        return self

    def limit(self, value):
        self.rows = self.rows[:value]
        return self

    def execute(self):
        return _Response(self.rows)


class _Client:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        if name != "authorized_students":
            raise AssertionError(name)
        return _Query(list(self.rows))


class AcademyAccessTests(unittest.TestCase):
    def setUp(self):
        academy_access.academy_student_by_email.clear()

    def test_active_diplomado_email_is_recognized(self):
        rows = [{
            "display_name": "Alumno",
            "email": "alumno@example.com",
            "course_id": academy_access.DIPLOMADO_COURSE_ID,
            "active": True,
        }]
        with patch.object(academy_access, "academy_supabase_client", return_value=_Client(rows)):
            result = academy_access.academy_student_by_email(" ALUMNO@example.com ")
        self.assertEqual(result["display_name"], "Alumno")

    def test_inactive_student_is_not_recognized(self):
        rows = [{
            "display_name": "Alumno",
            "email": "alumno@example.com",
            "course_id": academy_access.DIPLOMADO_COURSE_ID,
            "active": False,
        }]
        with patch.object(academy_access, "academy_supabase_client", return_value=_Client(rows)):
            self.assertIsNone(academy_access.academy_student_by_email("alumno@example.com"))

    def test_invalid_email_does_not_query_supabase(self):
        with patch.object(academy_access, "academy_supabase_client") as client:
            self.assertIsNone(academy_access.academy_student_by_email("sin-correo"))
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
