from django.core.cache import cache
from django.test import TestCase

from employees.services.employee_service import EmployeeService

from .helpers import make_department, make_employee


class CacheTests(TestCase):
    def setUp(self):
        cache.clear()
        self.service = EmployeeService()
        self.dept = make_department()

    def test_second_statistics_call_uses_no_queries(self):
        self.service.get_statistics()
        with self.assertNumQueries(0):
            self.service.get_statistics()

    def test_plain_orm_save_clears_the_stats_cache(self):
        self.service.get_statistics()
        make_employee(self.dept)                  # bypasses the service, like the admin site
        self.assertEqual(self.service.get_statistics()['total'], 1)

    def test_departments_are_cached_then_refreshed_after_a_rename(self):
        self.service.get_departments()
        with self.assertNumQueries(0):
            self.service.get_departments()
        self.dept.name = 'Technology'
        self.dept.save()
        self.assertEqual(self.service.get_departments()[0]['name'], 'Technology')