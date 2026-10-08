from io import StringIO

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.management import call_command
from django.test import TransactionTestCase
from django.urls import reverse

from employees.consumers import EMPLOYEE_GROUP, EmployeeUpdatesConsumer

from .test_views import ViewTestBase


class WebSocketTests(TransactionTestCase):
    def setUp(self):
        call_command('setup_roles', stdout=StringIO())
        self.viewer = User.objects.create_user('ws_viewer', password='Pass12345!x')
        self.viewer.groups.add(Group.objects.get(name='Viewer'))
        self.nobody = User.objects.create_user('ws_nobody', password='Pass12345!x')

    async def open_socket(self, user):
        communicator = WebsocketCommunicator(EmployeeUpdatesConsumer.as_asgi(), '/ws/employees/')
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        return communicator, connected

    async def test_anonymous_user_is_rejected(self):
        _, connected = await self.open_socket(AnonymousUser())
        self.assertFalse(connected)

    async def test_user_without_permission_is_rejected(self):
        _, connected = await self.open_socket(self.nobody)
        self.assertFalse(connected)

    async def test_viewer_receives_a_broadcast(self):
        communicator, connected = await self.open_socket(self.viewer)
        self.assertTrue(connected)
        await get_channel_layer().group_send(EMPLOYEE_GROUP, {
            'type': 'employee.event',
            'payload': {'type': 'employee', 'message': 'Marcus Osborn was added'},
        })
        message = await communicator.receive_json_from()
        self.assertEqual(message['message'], 'Marcus Osborn was added')
        await communicator.disconnect()

    async def test_ping_gets_pong(self):
        communicator, _ = await self.open_socket(self.viewer)
        await communicator.send_json_to({'action': 'ping'})
        self.assertEqual(await communicator.receive_json_from(), {'type': 'pong'})
        await communicator.disconnect()


class DashboardTests(ViewTestBase):
    def test_anonymous_is_redirected_to_login(self):
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 302)

    def test_viewer_sees_the_dashboard(self):
        self.login('viewer_u')
        response = self.client.get(reverse('dashboard:home'))
        self.assertContains(response, 'Total employees')