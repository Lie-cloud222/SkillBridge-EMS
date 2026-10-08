from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

ROLES = {
    'Admin': [
        'add_employee', 'change_employee', 'delete_employee', 'view_employee',
        'add_department', 'change_department', 'delete_department', 'view_department',
    ],
    'HR Manager': [
        'add_employee', 'change_employee', 'view_employee',
        'view_department',
    ],
    'Viewer': [
        'view_employee',
        'view_department',
    ],
}


class Command(BaseCommand):
    help = 'Creates the Admin, HR Manager and Viewer groups with their permissions.'

    def handle(self, *args, **options):
        for role_name, codenames in ROLES.items():
            group, created = Group.objects.get_or_create(name=role_name)
            permissions = Permission.objects.filter(
                content_type__app_label='employees',
                codename__in=codenames,
            )
            group.permissions.set(permissions)
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'{status} group "{role_name}" with {permissions.count()} permissions'
            ))