import logging
from django.db import DatabaseError

logger = logging.getLogger(__name__)

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, FormView, ListView

from .forms import EmployeeForm
from .models import Department, Employee
from .services.employee_service import EmployeeService

service = EmployeeService()          # one shared service object for all views


def hello(request):
    return render(request, 'employees/hello.html')


class EmployeeListView(PermissionRequiredMixin, ListView):
    permission_required = 'employees.view_employee'
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        department = self.request.GET.get('department', '')
        status = self.request.GET.get('status', '')
        department = int(department) if department.isdigit() else None
        return service.list_employees(q or None, department, status or None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        context.update({
            'q': self.request.GET.get('q', ''),
            'selected_department': self.request.GET.get('department', ''),
            'selected_status': self.request.GET.get('status', ''),
            'departments': Department.objects.all(),
            'statuses': Employee.Status.choices,
            'querystring': params.urlencode(),
        })
        return context


class EmployeeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'employees.view_employee'
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_object(self, queryset=None):
        employee = service.get_employee_by_id(self.kwargs['pk'])
        if employee is None:
            raise Http404("Employee not found.")
        return employee


class EmployeeCreateView(PermissionRequiredMixin, FormView):
    permission_required = 'employees.add_employee'
    template_name = 'employees/employee_form.html'
    form_class = EmployeeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Employee'
        return context

    def form_valid(self, form):
        user = self.request.user.username
        try:
            employee = service.create_employee(form.cleaned_data)
        except ValueError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        except ValidationError as error:
            for message in error.messages:
                form.add_error(None, message)
            return self.form_invalid(form)
        except DatabaseError:
            logger.exception("Database error creating an employee (user %s)", user)
            form.add_error(None, "Something went wrong while saving. Please try again.")
            return self.form_invalid(form)
        messages.success(self.request, f"{employee.full_name} was added.")
        return redirect('employees:employee-list')
    
class EmployeeUpdateView(PermissionRequiredMixin, FormView):
    permission_required = 'employees.change_employee'
    template_name = 'employees/employee_form.html'
    form_class = EmployeeForm

    def get_employee(self):
        if not hasattr(self, '_employee'):
            employee = service.get_employee_by_id(self.kwargs['pk'])
            if employee is None:
                raise Http404("Employee not found.")
            self._employee = employee
        return self._employee

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_employee()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Employee'
        return context

    def form_valid(self, form):
        user = self.request.user.username
        pk = self.get_employee().pk
        try:
            employee = service.update_employee(pk, form.cleaned_data)
        except ValueError as error:
            logger.warning("Update of pk=%s rejected for user %s: %s", pk, user, error)
            form.add_error(None, str(error))
            return self.form_invalid(form)
        except ValidationError as error:
            logger.warning("Update of pk=%s failed validation for user %s: %s", pk, user, error.messages)
            for message in error.messages:
                form.add_error(None, message)
            return self.form_invalid(form)
        except DatabaseError:
            logger.exception("Database error updating employee pk=%s (user %s)", pk, user)
            form.add_error(None, "Something went wrong while saving. Please try again.")
            return self.form_invalid(form)
        logger.info("User %s updated employee pk=%s", user, pk)
        messages.success(self.request, f"{employee.full_name} was updated.")
        return redirect('employees:employee-detail', pk=employee.pk)


class EmployeeDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'employees.delete_employee'
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    context_object_name = 'employee'
    success_url = reverse_lazy('employees:employee-list')

    def form_valid(self, form):
        self.object = self.get_object()
        name, pk = self.object.full_name, self.object.pk
        user = self.request.user.username
        try:
            service.delete_employee(pk)
        except DatabaseError:
            logger.exception("Database error deleting employee pk=%s (user %s)", pk, user)
            messages.error(self.request, "The employee could not be deleted. Please try again.")
            return HttpResponseRedirect(self.success_url)
        logger.info("User %s deleted employee pk=%s", user, pk)
        messages.success(self.request, f"{name} was deleted.")
        return HttpResponseRedirect(self.success_url)