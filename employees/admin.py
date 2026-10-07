from django.contrib import admin
from .models import Department, Employee
# Register your models here.
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_count']
    search_fields = ['name']

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employees'

    
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
        list_display = [
            'employee_id', 
            'full_name', 
            'email', 
            'department',
            'employment_type',
            'status',
            'is_active',
        ]

        list_filter = [
            'department',
            'status',
            'employment_type',
            'is_active',
        ]

        search_fields = [
            'first_name',
            'last_name',
            'email',
            'employee_id',
        ]

        list_select_related = ['department']

        readonly_fields = [
            'created_at',
            'updated_at',
        ]

        ordering = [
            'last_name',
            'first_name'
        ]