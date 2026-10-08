from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee
from .helpers import form_data, make_department, make_employee

PASSWORD = 'Pass12345!x'


class ViewTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=StringIO())          # builds the 3 groups
        cls.dept = make_department()
        cls.employee = make_employee(cls.dept)
        for username, group in [('admin_u', 'Admin'), ('hr_u', 'HR Manager'), ('viewer_u', 'Viewer')]:
            user = User.objects.create_user(username, password=PASSWORD)
            user.groups.add(Group.objects.get(name=group))

    def login(self, username):
        self.assertTrue(self.client.login(username=username, password=PASSWORD))

    def url(self, name, with_pk=False):
        return reverse(f'employees:{name}', kwargs={'pk': self.employee.pk} if with_pk else None)


class AnonymousAccessTests(ViewTestBase):
    def test_every_employee_page_redirects_to_login(self):
        pages = [self.url('employee-list'), self.url('employee-add'),
                 self.url('employee-detail', True), self.url('employee-edit', True),
                 self.url('employee-delete', True)]
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class ViewerTests(ViewTestBase):
    def setUp(self):
        self.login('viewer_u')

    def test_can_view_list_but_sees_no_edit_or_delete_buttons(self):
        response = self.client.get(self.url('employee-list'))
        self.assertContains(response, 'Marcus')
        self.assertNotContains(response, '/edit/')
        self.assertNotContains(response, '/delete/')

    def test_cannot_see_salary(self):
        response = self.client.get(self.url('employee-detail', True))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<th>Salary</th>')

    def test_forbidden_pages_return_403_with_friendly_page(self):
        for name in ('employee-add', 'employee-edit', 'employee-delete'):
            with self.subTest(page=name):
                response = self.client.get(self.url(name, name != 'employee-add'))
                self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

    def test_cannot_delete_by_posting_directly(self):
        response = self.client.post(self.url('employee-delete', True))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Employee.objects.filter(pk=self.employee.pk).exists())


class HRManagerTests(ViewTestBase):
    def setUp(self):
        self.login('hr_u')

    def test_can_add_an_employee(self):
        response = self.client.post(self.url('employee-add'), form_data(
            self.dept, employee_id='EMP002', email='New@Example.com', first_name='jane'))
        self.assertRedirects(response, self.url('employee-list'))
        created = Employee.objects.get(employee_id='EMP002')
        self.assertEqual(created.email, 'new@example.com')          # tidied by the form
        self.assertEqual(created.first_name, 'Jane')

    def test_can_edit_an_employee_and_sees_salary(self):
        response = self.client.post(self.url('employee-edit', True),
                                    form_data(self.dept, job_title='Lead Developer'))
        self.assertRedirects(response, self.url('employee-detail', True))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.job_title, 'Lead Developer')
        self.assertContains(self.client.get(self.url('employee-detail', True)), '<th>Salary</th>')

    def test_cannot_delete(self):
        self.assertEqual(self.client.get(self.url('employee-delete', True)).status_code, 403)


class AdminTests(ViewTestBase):
    def setUp(self):
        self.login('admin_u')

    def test_delete_asks_for_confirmation_then_deletes(self):
        page = self.client.get(self.url('employee-delete', True))
        self.assertContains(page, 'Are you sure')
        response = self.client.post(self.url('employee-delete', True))
        self.assertRedirects(response, self.url('employee-list'))
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())


class ListFeatureTests(ViewTestBase):
    def setUp(self):
        self.login('viewer_u')
        self.finance = make_department('Finance')
        make_employee(self.finance, employee_id='EMP002', first_name='Thandi', last_name='Nkosi',
                      email='thandi@example.com', status='on_leave')

    def names(self, response):
        return [e.first_name for e in response.context['employees']]

    def test_search(self):
        response = self.client.get(self.url('employee-list'), {'q': 'thandi'})
        self.assertEqual(self.names(response), ['Thandi'])

    def test_filter_by_department_and_status(self):
        response = self.client.get(self.url('employee-list'), {'department': self.dept.pk})
        self.assertEqual(self.names(response), ['Marcus'])
        response = self.client.get(self.url('employee-list'), {'status': 'on_leave'})
        self.assertEqual(self.names(response), ['Thandi'])

    def test_no_matches_shows_message(self):
        response = self.client.get(self.url('employee-list'), {'q': 'zzzz'})
        self.assertContains(response, 'No employees match')

    def test_garbage_department_value_does_not_crash(self):
        response = self.client.get(self.url('employee-list'), {'department': 'abc'})
        self.assertEqual(response.status_code, 200)


class ErrorConditionTests(ViewTestBase):
    def setUp(self):
        self.login('hr_u')

    def test_duplicate_email_shows_error_and_saves_nothing(self):
        response = self.client.post(self.url('employee-add'), form_data(self.dept, employee_id='EMP002'))
        self.assertEqual(response.status_code, 200)                 # form shown again, no redirect
        self.assertContains(response, 'already exists')
        self.assertEqual(Employee.objects.count(), 1)

    def test_future_hire_date_shows_error(self):
        response = self.client.post(self.url('employee-add'), form_data(
            self.dept, employee_id='EMP002', email='x@example.com', hire_date='2999-01-01'))
        self.assertContains(response, 'cannot be in the future')
        self.assertEqual(Employee.objects.count(), 1)

    def test_missing_employee_gives_404(self):
        response = self.client.get(reverse('employees:employee-detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    def test_database_failure_is_handled_and_logged(self):
        with patch('employees.views.service.create_employee', side_effect=DatabaseError('boom')):
            with self.assertLogs('employees', level='ERROR'):
                response = self.client.post(self.url('employee-add'), form_data(
                    self.dept, employee_id='EMP002', email='x@example.com'))
        self.assertEqual(response.status_code, 200)                 # no crash, no 500 page
        self.assertContains(response, 'Something went wrong')
        self.assertNotContains(response, 'boom')                    # technical detail not leaked