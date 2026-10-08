from types import SimpleNamespace

from django.core.cache import cache
from django.test import SimpleTestCase

from employees.services.employee_service import EmployeeService


class FakeRepository:
    """An in-memory stand-in for EmployeeRepository."""

    def __init__(self):
        self.rows = {}
        self.next_pk = 1
        self.create_calls = 0
        self.count_calls = 0

    def email_exists(self, email, exclude_id=None):
        return any(r.email.lower() == email.lower() and pk != exclude_id
                   for pk, r in self.rows.items())

    def employee_id_exists(self, employee_id, exclude_id=None):
        return any(r.employee_id.lower() == employee_id.lower() and pk != exclude_id
                   for pk, r in self.rows.items())

    def create(self, data):
        pk = self.next_pk
        self.next_pk += 1
        self.create_calls += 1
        self.rows[pk] = SimpleNamespace(pk=pk, **data)
        return self.rows[pk]

    def get_by_id(self, pk):
        return self.rows.get(pk)

    def update(self, pk, data):
        for field, value in data.items():
            setattr(self.rows[pk], field, value)
        return self.rows[pk]

    def delete(self, pk):
        return self.rows.pop(pk, None) is not None

    def count(self, **filters):
        self.count_calls += 1
        return len(self.rows)

    def count_by_department(self):
        return {}


class EmployeeServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.repo = FakeRepository()
        self.service = EmployeeService(repository=self.repo)
        self.data = {'employee_id': 'EMP001', 'email': 'a@example.com'}

    def test_create_stores_the_employee(self):
        employee = self.service.create_employee(self.data)
        self.assertEqual(employee.pk, 1)
        self.assertEqual(self.repo.create_calls, 1)

    def test_duplicate_email_is_rejected_before_saving(self):
        self.service.create_employee(self.data)
        with self.assertRaisesMessage(ValueError, 'email already exists'):
            self.service.create_employee({'employee_id': 'EMP002', 'email': 'A@EXAMPLE.COM'})
        self.assertEqual(self.repo.create_calls, 1)

    def test_duplicate_employee_id_is_rejected(self):
        self.service.create_employee(self.data)
        with self.assertRaisesMessage(ValueError, 'already in use'):
            self.service.create_employee({'employee_id': 'emp001', 'email': 'b@example.com'})

    def test_update_unknown_employee_raises(self):
        with self.assertRaisesMessage(ValueError, 'not found'):
            self.service.update_employee(99, {'email': 'x@example.com'})

    def test_update_to_an_email_used_by_someone_else_is_rejected(self):
        self.service.create_employee(self.data)
        self.service.create_employee({'employee_id': 'EMP002', 'email': 'b@example.com'})
        with self.assertRaises(ValueError):
            self.service.update_employee(2, {'email': 'a@example.com'})

    def test_update_keeping_your_own_email_is_allowed(self):
        self.service.create_employee(self.data)
        updated = self.service.update_employee(1, {'email': 'a@example.com'})
        self.assertEqual(updated.email, 'a@example.com')

    def test_delete_reports_whether_anything_was_deleted(self):
        self.service.create_employee(self.data)
        self.assertTrue(self.service.delete_employee(1))
        self.assertFalse(self.service.delete_employee(1))

    def test_statistics_are_cached(self):
        self.service.get_statistics()
        calls_after_first = self.repo.count_calls
        self.service.get_statistics()
        self.assertEqual(self.repo.count_calls, calls_after_first)    # second call used the cache

    def test_writing_clears_the_statistics_cache(self):
        cache.set(EmployeeService.CACHE_KEY_STATS, {'total': 99})
        self.service.create_employee(self.data)
        self.assertIsNone(cache.get(EmployeeService.CACHE_KEY_STATS))

    def test_rejected_create_is_logged(self):
        self.service.create_employee(self.data)
        with self.assertLogs('employees', level='WARNING') as logs:
            with self.assertRaises(ValueError):
                self.service.create_employee({'employee_id': 'EMP002', 'email': 'a@example.com'})
        self.assertIn('duplicate email', logs.output[0])