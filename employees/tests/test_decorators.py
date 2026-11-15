from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from employees.decorators import audit_action, no_store, rate_limit


class FakeUser:
    is_authenticated = True
    username = 'hr_u'
    pk = 7


def make_request(user=None, method='post', path='/employees/add/'):
    request = getattr(RequestFactory(), method)(path)
    request.user = user or FakeUser()
    return request


class AuditActionTests(SimpleTestCase):
    def test_logs_before_and_after_a_successful_view(self):
        @audit_action('create employee')
        def view(request):
            return HttpResponse(status=302)

        with self.assertLogs('employees.audit', level='INFO') as logs:
            response = view(make_request())
        self.assertEqual(response.status_code, 302)          # response is untouched
        self.assertEqual(len(logs.records), 2)
        self.assertIn('AUDIT start', logs.output[0])
        self.assertIn('action=create employee', logs.output[0])
        self.assertIn('user=hr_u', logs.output[0])
        self.assertIn('AUDIT done', logs.output[1])
        self.assertIn('status=302', logs.output[1])

    def test_anonymous_user_is_recorded_as_anonymous(self):
        @audit_action('view employee')
        def view(request):
            return HttpResponse()

        with self.assertLogs('employees.audit', level='INFO') as logs:
            view(make_request(AnonymousUser()))
        self.assertIn('user=anonymous', logs.output[0])

    def test_error_status_is_logged_as_a_warning(self):
        @audit_action('create employee')
        def view(request):
            return HttpResponse(status=403)

        with self.assertLogs('employees.audit', level='WARNING') as logs:
            view(make_request())
        self.assertIn('WARNING', logs.output[0])
        self.assertIn('status=403', logs.output[0])

    def test_refused_request_is_logged_and_still_raised(self):
        @audit_action('delete employee')
        def view(request):
            raise PermissionDenied

        with self.assertLogs('employees.audit', level='WARNING') as logs:
            with self.assertRaises(PermissionDenied):
                view(make_request())
        self.assertIn('AUDIT refused', logs.output[0])

    def test_missing_page_is_logged_and_still_raised(self):
        @audit_action('view employee')
        def view(request):
            raise Http404

        with self.assertLogs('employees.audit', level='WARNING'):
            with self.assertRaises(Http404):
                view(make_request())

    def test_unexpected_error_is_logged_with_traceback_and_reraised(self):
        @audit_action('update employee')
        def view(request):
            raise RuntimeError('boom')

        with self.assertLogs('employees.audit', level='ERROR') as logs:
            with self.assertRaises(RuntimeError):
                view(make_request())
        self.assertIn('AUDIT error', logs.output[0])
        self.assertIn('RuntimeError', logs.output[0])         # traceback is included

    def test_form_data_is_never_logged(self):
        @audit_action('create employee')
        def view(request):
            return HttpResponse()

        request = RequestFactory().post('/employees/add/', {'salary': '99999', 'email': 'a@b.com'})
        request.user = FakeUser()
        with self.assertLogs('employees.audit', level='INFO') as logs:
            view(request)
        combined = ' '.join(logs.output)
        self.assertNotIn('99999', combined)
        self.assertNotIn('a@b.com', combined)

    def test_keeps_the_view_name_and_arguments(self):
        @audit_action('view employee')
        def employee_detail(request, pk):
            """Docstring."""
            return HttpResponse(str(pk))

        self.assertEqual(employee_detail.__name__, 'employee_detail')
        self.assertEqual(employee_detail.__doc__, 'Docstring.')
        with self.assertLogs('employees.audit', level='INFO'):
            self.assertEqual(employee_detail(make_request(), pk=5).content, b'5')


class RateLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def make_view(self, scope='test', calls=2):
        calls_made = []

        @rate_limit(scope, calls=calls, period=60)
        def view(request):
            calls_made.append(1)
            return HttpResponse('ok')

        return view, calls_made

    def test_allows_requests_up_to_the_limit(self):
        view, calls_made = self.make_view(calls=2)
        self.assertEqual(view(make_request()).status_code, 200)
        self.assertEqual(view(make_request()).status_code, 200)
        self.assertEqual(len(calls_made), 2)

    def test_blocks_the_next_request_without_running_the_view(self):
        view, calls_made = self.make_view(calls=2)
        view(make_request())
        view(make_request())
        with self.assertLogs('employees.audit', level='WARNING') as logs:
            response = view(make_request())
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '60')
        self.assertEqual(len(calls_made), 2)                  # the view did NOT run a third time
        self.assertIn('rate-limited', logs.output[0])

    def test_each_user_has_their_own_allowance(self):
        view, _ = self.make_view(calls=1)

        class Other(FakeUser):
            username, pk = 'other', 8

        view(make_request())
        self.assertEqual(view(make_request()).status_code, 429)
        self.assertEqual(view(make_request(Other())).status_code, 200)

    def test_each_scope_is_counted_separately(self):
        first, _ = self.make_view(scope='a', calls=1)
        second, _ = self.make_view(scope='b', calls=1)
        first(make_request())
        self.assertEqual(second(make_request()).status_code, 200)

    def test_anonymous_visitors_are_counted_by_ip(self):
        view, _ = self.make_view(calls=1)
        view(make_request(AnonymousUser()))
        self.assertEqual(view(make_request(AnonymousUser())).status_code, 429)

    def test_window_resets_when_the_cache_entry_expires(self):
        view, _ = self.make_view(calls=1)
        view(make_request())
        self.assertEqual(view(make_request()).status_code, 429)
        cache.clear()                                         # simulates the period ending
        self.assertEqual(view(make_request()).status_code, 200)


class NoStoreTests(SimpleTestCase):
    def test_adds_headers_after_the_view_runs(self):
        @no_store
        def view(request):
            return HttpResponse('salary page')

        response = view(make_request(method='get'))
        self.assertEqual(response.content, b'salary page')     # body untouched
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('private', response['Cache-Control'])
        self.assertIn('no-cache', response['Cache-Control'])


class HealthCheckTests(TestCase):
    def test_reports_ok_without_login(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': 'ok'})
        self.assertIn('no-cache', response['Cache-Control'])

    def test_post_is_not_allowed(self):
        self.assertEqual(self.client.post(reverse('health')).status_code, 405)

    def test_reports_503_when_the_database_is_down(self):
        from django.db import DatabaseError
        with patch('employees.health.connection.cursor', side_effect=DatabaseError('down')):
            with self.assertLogs('employees.health', level='ERROR'):
                response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'error')
        self.assertNotIn('down', response.content.decode())   # no internal detail leaked
