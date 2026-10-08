from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Department, Employee
from .services.employee_service import EmployeeService


@receiver([post_save, post_delete], sender=Employee)
def employee_changed(sender, **kwargs):
    cache.delete(EmployeeService.CACHE_KEY_STATS)


@receiver([post_save, post_delete], sender=Department)
def department_changed(sender, **kwargs):
    cache.delete(EmployeeService.CACHE_KEY_DEPARTMENTS)
    cache.delete(EmployeeService.CACHE_KEY_STATS)