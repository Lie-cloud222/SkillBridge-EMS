from django.shortcuts import render
import logging

# Create your views here.
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from employees.models import Employee
from employees.services.employee_service import EmployeeService

from .permissions import EmployeePermissions
from .serializers import EmployeeSerializer

logger = logging.getLogger('employees.api')
service = EmployeeService()


class EmployeeViewSet(ViewSet):
    permission_classes = [EmployeePermissions]
    queryset = Employee.objects.none()      # DRF's permission class needs a queryset to find the model

    def _get_or_404(self, pk):
        employee = service.get_employee_by_id(pk)
        if employee is None:
            raise NotFound('Employee not found.')
        return employee

    def list(self, request):
        """GET /api/v1/employees/  and  ?search=...&department=...&status=..."""
        search = request.query_params.get('search', '').strip() or None
        department = request.query_params.get('department', '')
        status_filter = request.query_params.get('status', '').strip() or None
        department = int(department) if department.isdigit() else None
        employees = service.list_employees(search, department, status_filter)
        return Response(EmployeeSerializer(employees, many=True).data)

    def retrieve(self, request, pk=None):
        """GET /api/v1/employees/<id>/"""
        return Response(EmployeeSerializer(self._get_or_404(pk)).data)

    def create(self, request):
        """POST /api/v1/employees/"""
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.setdefault('salary', 0)     # salary is hidden from the API; set the real value on the website
        try:
            employee = service.create_employee(data)
        except ValueError as error:
            raise ValidationError({'detail': str(error)})
        except DjangoValidationError as error:
            raise ValidationError({'detail': error.messages})
        logger.info("API: user %s created employee pk=%s", request.user.username, employee.pk)
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """PUT /api/v1/employees/<id>/"""
        self._get_or_404(pk)
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            employee = service.update_employee(int(pk), dict(serializer.validated_data))
        except ValueError as error:
            raise ValidationError({'detail': str(error)})
        except DjangoValidationError as error:
            raise ValidationError({'detail': error.messages})
        logger.info("API: user %s updated employee pk=%s", request.user.username, pk)
        return Response(EmployeeSerializer(employee).data)

    def destroy(self, request, pk=None):
        """DELETE /api/v1/employees/<id>/"""
        self._get_or_404(pk)
        service.delete_employee(int(pk))
        logger.info("API: user %s deleted employee pk=%s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """GET /api/v1/employees/stats/"""
        return Response(service.get_statistics())