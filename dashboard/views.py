from django.shortcuts import render
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView

# Create your views here.
from employees.services.employee_service import EmployeeService

service = EmployeeService()


class DashboardView(PermissionRequiredMixin, TemplateView):
    permission_required = 'employees.view_employee'
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = service.get_statistics()
        context['recent'] = service.recent_employees(5)
        return context