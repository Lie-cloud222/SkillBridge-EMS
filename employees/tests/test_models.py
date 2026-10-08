from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from employees.models import Employee
from .helpers import employee_data, make_department, make_employee


class EmployeeModelTests(TestCase):
    def setUp(self):
        self.dept = make_department()

    def test_str_and_full_name(self):
        employee = make_employee(self.dept)
        self.assertEqual(str(employee), 'Marcus Osborn (EMP001)')
        self.assertEqual(employee.full_name, 'Marcus Osborn')

    def test_valid_employee_passes_validation(self):
        Employee(**employee_data(self.dept)).full_clean()      # raises nothing

    def test_blank_phone_is_allowed(self):
        Employee(**employee_data(self.dept, phone_number='')).full_clean()

    def test_future_hire_date_is_rejected(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        employee = Employee(**employee_data(self.dept, hire_date=tomorrow))
        with self.assertRaises(ValidationError) as ctx:
            employee.full_clean()
        self.assertIn('hire_date', ctx.exception.message_dict)

    def test_negative_salary_is_rejected(self):
        employee = Employee(**employee_data(self.dept, salary=-1))
        with self.assertRaises(ValidationError) as ctx:
            employee.full_clean()
        self.assertIn('salary', ctx.exception.message_dict)

    def test_invalid_phone_is_rejected(self):
        employee = Employee(**employee_data(self.dept, phone_number='abc'))
        with self.assertRaises(ValidationError) as ctx:
            employee.full_clean()
        self.assertIn('phone_number', ctx.exception.message_dict)

    def test_duplicate_email_is_rejected(self):
        make_employee(self.dept)
        duplicate = Employee(**employee_data(self.dept, employee_id='EMP002'))
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn('email', ctx.exception.message_dict)

    def test_terminated_employee_cannot_be_active(self):
        employee = Employee(**employee_data(self.dept, status='terminated', is_active=True))
        with self.assertRaises(ValidationError):
            employee.full_clean()

    def test_department_with_employees_cannot_be_deleted(self):
        make_employee(self.dept)
        with self.assertRaises(ProtectedError):
            self.dept.delete()