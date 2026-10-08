from django.test import Client
from django.urls import reverse

from .helpers import make_department, make_employee
from .test_views import PASSWORD, ViewTestBase


class SessionFilterTests(ViewTestBase):
    def setUp(self):
        self.login('viewer_u')
        self.list_url = reverse('employees:employee-list')
        make_employee(make_department('Finance'), employee_id='EMP002', first_name='Thandi',
                      last_name='Nkosi', email='thandi@example.com')

    def names(self, response):
        return {e.first_name for e in response.context['employees']}

    def test_filters_are_remembered_between_requests(self):
        self.client.get(self.list_url, {'q': 'thandi'})
        response = self.client.get(self.list_url)             # no parameters this time
        self.assertEqual(self.names(response), {'Thandi'})
        self.assertTrue(response.context['restored'])

    def test_clear_forgets_the_filters(self):
        self.client.get(self.list_url, {'q': 'thandi'})
        response = self.client.get(self.list_url, {'clear': '1'})
        self.assertEqual(self.names(response), {'Marcus', 'Thandi'})
        self.assertEqual(self.names(self.client.get(self.list_url)), {'Marcus', 'Thandi'})

    def test_filters_belong_to_one_user(self):
        self.client.get(self.list_url, {'q': 'thandi'})
        other = Client()
        other.login(username='hr_u', password=PASSWORD)
        self.assertEqual(self.names(other.get(self.list_url)), {'Marcus', 'Thandi'})