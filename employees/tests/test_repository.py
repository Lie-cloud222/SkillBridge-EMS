from django.core.exceptions import ValidationError
from django.test import TestCase

from employees.models import Employee
from employees.repositories.employee_repository import EmployeeRepository
from .helpers import employee_data, make_department, make_employee


class EmployeeRepositoryTests(TestCase):
    def setUp(self):
        self.repo = EmployeeRepository()
        self.eng = make_department('Engineering')
        self.fin = make_department('Finance')
        self.marcus = make_employee(self.eng)
        self.thandi = make_employee(
            self.fin, employee_id='EMP002', first_name='Thandi', last_name='Nkosi',
            email='thandi@example.com', status='on_leave',
        )

    def test_get_by_id_found_and_missing(self):
        self.assertEqual(self.repo.get_by_id(self.marcus.pk), self.marcus)
        self.assertIsNone(self.repo.get_by_id(9999))

    def test_search_matches_part_of_a_name(self):
        self.assertEqual(list(self.repo.search('mar')), [self.marcus])

    def test_search_and_filter_by_department_and_status(self):
        self.assertEqual(list(self.repo.search_and_filter(department=self.fin.pk)), [self.thandi])
        self.assertEqual(list(self.repo.search_and_filter(status='on_leave')), [self.thandi])
        self.assertEqual(list(self.repo.search_and_filter(query='mar', status='on_leave')), [])

    def test_email_exists_is_case_insensitive_and_can_exclude_self(self):
        self.assertTrue(self.repo.email_exists('MARCUS.O@EXAMPLE.COM'))
        self.assertFalse(self.repo.email_exists('marcus.o@example.com', exclude_id=self.marcus.pk))

    def test_employee_id_exists(self):
        self.assertTrue(self.repo.employee_id_exists('emp001'))
        self.assertFalse(self.repo.employee_id_exists('EMP999'))

    def test_create_saves_a_valid_employee(self):
        data = employee_data(self.eng, employee_id='EMP003', email='new@example.com')
        created = self.repo.create(data)
        self.assertTrue(Employee.objects.filter(pk=created.pk).exists())

    def test_create_rejects_invalid_data_and_saves_nothing(self):
        data = employee_data(self.eng, employee_id='EMP003', email='new@example.com', salary=-5)
        with self.assertRaises(ValidationError):
            self.repo.create(data)
        self.assertEqual(Employee.objects.count(), 2)

    def test_update_changes_the_row(self):
        self.repo.update(self.marcus.pk, {'job_title': 'Lead Developer'})
        self.marcus.refresh_from_db()
        self.assertEqual(self.marcus.job_title, 'Lead Developer')

    def test_update_rejects_invalid_data_and_keeps_old_value(self):
        with self.assertRaises(ValidationError):
            self.repo.update(self.marcus.pk, {'salary': -1})
        self.marcus.refresh_from_db()
        self.assertEqual(self.marcus.salary, 25000)

    def test_update_missing_employee_returns_none(self):
        self.assertIsNone(self.repo.update(9999, {'job_title': 'x'}))

    def test_delete_returns_true_then_false(self):
        self.assertTrue(self.repo.delete(self.marcus.pk))
        self.assertFalse(self.repo.delete(self.marcus.pk))

    def test_count_by_department(self):
        self.assertEqual(self.repo.count_by_department(), {'Engineering': 1, 'Finance': 1})