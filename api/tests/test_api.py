from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from rest_framework.test import APITestCase

from employees.models import Employee
from employees.tests.helpers import make_department, make_employee

PASSWORD = 'Pass12345!x'
URL = '/api/v1/employees/'


class EmployeeApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=StringIO())
        cls.dept = make_department()
        cls.kayden = make_employee(cls.dept, first_name='Kayden', email='kayden.d@example.com')
        cls.other = make_employee(
            cls.dept, employee_id='EMP002', first_name='Brandon',
            email='brandon@example.com', is_active=False, status='terminated',
        )
        for username, group in [('admin_u', 'Admin'), ('hr_u', 'HR Manager'), ('viewer_u', 'Viewer')]:
            user = User.objects.create_user(username, password=PASSWORD)
            user.groups.add(Group.objects.get(name=group))

    def as_user(self, username):
        self.client.login(username=username, password=PASSWORD)

    def payload(self, **overrides):
        data = {
            'employee_id': 'EMP100',
            'first_name': 'Thandi',
            'last_name': 'Nkosi',
            'email': 'thandi@example.com',
            'phone_number': '0821234567',
            'department': self.dept.pk,
            'job_title': 'Accountant',
            'employment_type': 'full_time',
            'hire_date': '2021-03-01',
            'status': 'active',
            'is_active': True,
        }
        data.update(overrides)
        return data

    # ---------- access control ----------
    def test_anonymous_gets_no_data(self):
        response = self.client.get(URL)
        self.assertIn(response.status_code, (401, 403))
        self.assertNotIn('Kayden', response.content.decode())

    def test_viewer_cannot_write(self):
        self.as_user('viewer_u')
        self.assertEqual(self.client.post(URL, self.payload(), format='json').status_code, 403)
        self.assertEqual(self.client.delete(f'{URL}{self.kayden.pk}/').status_code, 403)

    def test_hr_can_create_but_not_delete(self):
        self.as_user('hr_u')
        response = self.client.post(URL, self.payload(), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.delete(f'{URL}{self.kayden.pk}/').status_code, 403)

    def test_admin_can_delete(self):
        self.as_user('admin_u')
        self.assertEqual(self.client.delete(f'{URL}{self.other.pk}/').status_code, 204)
        self.assertFalse(Employee.objects.filter(pk=self.other.pk).exists())

    # ---------- reading ----------
    def test_list_and_detail(self):
        self.as_user('viewer_u')
        self.assertEqual(len(self.client.get(URL).json()), 2)
        detail = self.client.get(f'{URL}{self.kayden.pk}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['first_name'], 'Kayden')

    def test_salary_is_never_exposed(self):
        self.as_user('admin_u')
        self.assertNotIn('salary', self.client.get(f'{URL}{self.kayden.pk}/').json())

    def test_search_returns_only_matches(self):
        self.as_user('viewer_u')
        results = self.client.get(URL, {'search': 'Kayden'}).json()
        self.assertEqual([r['first_name'] for r in results], ['Kayden'])

    def test_stats(self):
        self.as_user('viewer_u')
        stats = self.client.get(f'{URL}stats/').json()
        self.assertEqual((stats['total'], stats['active'], stats['inactive']), (2, 1, 1))

    # ---------- error conditions ----------
    def test_missing_employee_is_404_json(self):
        self.as_user('viewer_u')
        response = self.client.get(f'{URL}9999/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Employee not found.')

    def test_duplicate_email_returns_400(self):
        self.as_user('hr_u')
        response = self.client.post(URL, self.payload(email='kayden.d@example.com'), format='json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_data_returns_400_not_500(self):
        self.as_user('hr_u')
        response = self.client.post(URL, self.payload(hire_date='2999-01-01'), format='json')
        self.assertEqual(response.status_code, 400)
