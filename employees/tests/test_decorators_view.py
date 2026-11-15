"""The decorators as they are applied to the real employee views.

These reuse ViewTestBase and form_data from your existing tests. If your
helpers live in a different module or have different names, adjust the two
imports below.
"""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from .helpers import form_data
from .test_views import ViewTestBase


class DecoratedViewTests(ViewTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def test_creating_an_employee_is_audited_before_and_after(self):
        self.login('hr_u')
        with self.assertLogs('employees.audit', level='INFO') as logs:
            self.client.post(self.url('employee-add'), form_data(
                self.dept, employee_id='EMP002', email='new@example.com'))
        text = '\n'.join(logs.output)
        self.assertIn('AUDIT start | action=create employee | user=hr_u', text)
        self.assertIn('AUDIT done | action=create employee | user=hr_u | status=302', text)

    def test_forbidden_attempt_is_audited_as_refused(self):
        self.login('viewer_u')
        with self.assertLogs('employees.audit', level='WARNING') as logs:
            response = self.client.get(self.url('employee-delete', True))
        self.assertEqual(response.status_code, 403)
        self.assertIn('AUDIT refused | action=delete employee | user=viewer_u', logs.output[0])

    def test_audit_log_never_contains_the_salary_or_email(self):
        self.login('hr_u')
        with self.assertLogs('employees.audit', level='INFO') as logs:
            self.client.post(self.url('employee-add'), form_data(
                self.dept, employee_id='EMP003', email='secret@example.com', salary='87654.00'))
        combined = ' '.join(logs.output)
        self.assertNotIn('87654', combined)
        self.assertNotIn('secret@example.com', combined)

    def test_detail_page_with_salary_is_not_cacheable(self):
        self.login('hr_u')
        response = self.client.get(self.url('employee-detail', True))
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])

    def test_rate_limit_stops_a_user_who_posts_too_often(self):
        self.login('hr_u')
        pk = User.objects.get(username='hr_u').pk
        cache.set(f'ratelimit:create-employee:user{pk}', 30, timeout=60)  # already at the limit
        response = self.client.post(self.url('employee-add'), form_data(
            self.dept, employee_id='EMP004', email='fast@example.com'))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '60')

    def test_opening_the_form_is_not_rate_limited(self):
        self.login('hr_u')
        pk = User.objects.get(username='hr_u').pk
        cache.set(f'ratelimit:create-employee:user{pk}', 30, timeout=60)
        self.assertEqual(self.client.get(self.url('employee-add')).status_code, 200)

    def test_health_check_needs_no_login(self):
        self.assertEqual(self.client.get(reverse('health')).status_code, 200)
