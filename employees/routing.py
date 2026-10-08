from django.urls import path

from .consumers import EmployeeUpdatesConsumer

websocket_urlpatterns = [
    path('ws/employees/', EmployeeUpdatesConsumer.as_asgi()),
]