from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from employees.forms import EmployeeForm
from .helpers import form_data, make_department, make_employee


class EmployeeFormTests(TestCase):
    def setUp(self):
        self.dept = make_department()

    def test_valid_data_is_accepted(self):
        self.assertTrue(EmployeeForm(data=form_data(self.dept)).is_valid())

    def test_input_is_tidied(self):
        form = EmployeeForm(data=form_data(
            self.dept, first_name='  jane ', email='  Jane@Example.COM ', employee_id=' emp100 '))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['first_name'], 'Jane')
        self.assertEqual(form.cleaned_data['email'], 'jane@example.com')
        self.assertEqual(form.cleaned_data['employee_id'], 'EMP100')

    def test_required_fields_are_enforced(self):
        form = EmployeeForm(data={})
        self.assertFalse(form.is_valid())
        for field in ('first_name', 'last_name', 'email', 'department', 'hire_date', 'salary'):
            self.assertIn(field, form.errors)

    def test_invalid_email_format(self):
        form = EmployeeForm(data=form_data(self.dept, email='not-an-email'))
        self.assertIn('email', EmployeeForm(data=form_data(self.dept, email='not-an-email')).errors)

    def test_duplicate_email_is_rejected(self):
        make_employee(self.dept)
        form = EmployeeForm(data=form_data(self.dept, employee_id='EMP002'))
        self.assertIn('email', form.errors)

    def test_editing_an_employee_may_keep_their_own_email(self):
        employee = make_employee(self.dept)
        form = EmployeeForm(data=form_data(self.dept, job_title='Lead'), instance=employee)
        self.assertTrue(form.is_valid(), form.errors)

    def test_future_hire_date_is_rejected(self):
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        form = EmployeeForm(data=form_data(self.dept, hire_date=future))
        self.assertIn('hire_date', form.errors)

    def test_negative_salary_and_bad_phone_are_rejected(self):
        form = EmployeeForm(data=form_data(self.dept, salary='-10', phone_number='abc'))
        self.assertIn('salary', form.errors)
        self.assertIn('phone_number', form.errors)

    def test_terminated_but_active_gives_a_form_level_error(self):
        form = EmployeeForm(data=form_data(self.dept, status='terminated'))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())