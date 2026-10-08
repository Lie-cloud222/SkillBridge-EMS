from datetime import date
from decimal import Decimal

from employees.models import Department, Employee


def make_department(name='Engineering'):
    return Department.objects.create(name=name)


def employee_data(department, **overrides):
    """Valid values for an Employee, as Python objects."""
    data = {
        'employee_id': 'EMP001',
        'first_name': 'Marcus',
        'last_name': 'Osborn',
        'email': 'marcus.o@example.com',
        'phone_number': '0821234567',
        'department': department,
        'job_title': 'Developer',
        'employment_type': 'full_time',
        'hire_date': date(2020, 1, 1),
        'salary': Decimal('25000.00'),
        'is_active': True,
        'status': 'active',
    }
    data.update(overrides)
    return data


def make_employee(department, **overrides):
    return Employee.objects.create(**employee_data(department, **overrides))


def form_data(department, **overrides):
    """The same values as strings, the way a browser submits a form."""
    data = {
        'employee_id': 'EMP001',
        'first_name': 'Marcus',
        'last_name': 'Osborn',
        'email': 'marcus.o@example.com',
        'phone_number': '0821234567',
        'department': department.pk,
        'job_title': 'Developer',
        'employment_type': 'full_time',
        'hire_date': '2020-01-01',
        'salary': '25000.00',
        'status': 'active',
        'is_active': 'on',
    }
    data.update(overrides)
    return data