from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from employees.models import Employee
from .helpers import form_data, make_department, make_employee
from .test_views import PASSWORD, ViewTestBase


class CsrfTests(ViewTestBase):
    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)           # Django's test client normally skips CSRF
        client.login(username='hr_u', password=PASSWORD)
        response = client.post(reverse('employees:employee-add'),
                               form_data(self.dept, employee_id='EMP002', email='x@example.com'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Employee.objects.count(), 1)

    def test_forms_contain_a_csrf_token(self):
        self.login('admin_u')
        print(sorted(self.client.session.keys()), User.objects.get(username='admin_u').get_all_permissions())
        for page in (reverse('employees:employee-add'),
                     reverse('employees:employee-delete', kwargs={'pk': self.employee.pk})):
            with self.subTest(page=page):
                self.assertContains(self.client.get(page), 'csrfmiddlewaretoken')


class AuthenticationTests(ViewTestBase):
    def test_wrong_password_is_refused(self):
        response = self.client.post(reverse('login'), {'username': 'hr_u', 'password': 'wrong'})
        self.assertContains(response, 'Incorrect username or password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        self.login('admin_u')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('employees:employee-list')).status_code, 302)

    def test_passwords_are_stored_hashed(self):
        user = User.objects.get(username='hr_u')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertIn('$', user.password)
        self.assertTrue(user.check_password(PASSWORD))


class UnsafeInputTests(ViewTestBase):
    def test_html_in_data_is_escaped_not_executed(self):
        make_employee(self.dept, employee_id='EMP002', email='x@example.com',
                      first_name='<script>alert(1)</script>')
        self.login('viewer_u')
        response = self.client.get(reverse('employees:employee-list'))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_sql_injection_text_is_treated_as_plain_search_text(self):
        self.login('viewer_u')
        response = self.client.get(reverse('employees:employee-list'), {'q': "' OR 1=1 --"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 0)   # did NOT return everyone
        self.assertEqual(Employee.objects.count(), 1)                       # nothing damaged