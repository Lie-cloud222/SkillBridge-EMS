import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .consumers import EMPLOYEE_GROUP
from .models import Department, Employee
from .services.employee_service import EmployeeService

logger = logging.getLogger(__name__)


def _clear_stats():
    cache.delete(EmployeeService.CACHE_KEY_STATS)


def _broadcast(message):
    """Push a message to every connected browser. Must never break a save."""
    try:
        async_to_sync(get_channel_layer().group_send)(EMPLOYEE_GROUP, {
            'type': 'employee.event',
            'payload': {'type': 'employee', 'message': message},
        })
    except Exception:
        logger.exception("Could not broadcast employee update")


@receiver(post_save, sender=Employee)
def employee_saved(sender, instance, created, **kwargs):
    _clear_stats()
    message = f"{instance.full_name} was {'added' if created else 'updated'}"
    transaction.on_commit(lambda: (_clear_stats(), _broadcast(message)))


@receiver(post_delete, sender=Employee)
def employee_deleted(sender, instance, **kwargs):
    _clear_stats()
    message = f"{instance.full_name} was deleted"
    transaction.on_commit(lambda: (_clear_stats(), _broadcast(message)))


@receiver([post_save, post_delete], sender=Department)
def department_changed(sender, **kwargs):
    cache.delete(EmployeeService.CACHE_KEY_DEPARTMENTS)
    _clear_stats()