from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

EMPLOYEE_GROUP = 'employee_updates'


class EmployeeUpdatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        allowed = False
        if user.is_authenticated:
            allowed = await database_sync_to_async(user.has_perm)('employees.view_employee')
        if not allowed:
            await self.close()
            return
        await self.channel_layer.group_add(EMPLOYEE_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(EMPLOYEE_GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):      # browser to server
        if content.get('action') == 'ping':
            await self.send_json({'type': 'pong'})

    async def employee_event(self, event):                # server to browser
        await self.send_json(event['payload'])