from typing import List, Optional
from django.db.models import Q, Count


class EmployeeRepository:
    @property
    def model(self):
        from employees.models import Employee
        return Employee

    def get_all(self) -> List:
        # Fixed: Employee has no created_by; department is the ForeignKey
        return self.model.objects.select_related('department').all()

    def get_by_id(self, pk: int) -> Optional["Employee"]:
        try:
            return self.model.objects.select_related('department').get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def search(self, query: str) -> List:
        return self.model.objects.select_related('department').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(employee_id__icontains=query)
        )

    def filter(self, department: int = None, is_active: bool = None) -> List:
        qs = self.model.objects.select_related('department').all()
        if department:
            qs = qs.filter(department_id=department)   # Fixed: compare by ID
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    def search_and_filter(self, query: str = None, department: int = None, status: str = None):
        qs = self.model.objects.select_related('department')
        if query:
            qs = qs.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query) |
                    Q(employee_id__icontains=query)
                    )
        if department:
            qs = qs.filter(department_id=department)
        if status:
            qs = qs.filter(status=status)
        return qs
         

    def create(self, data: dict):
        employee = self.model(**data)   # build it, not saved yet
        employee.full_clean()           # Fixed: runs your validators and clean()
        employee.save()
        return employee

    def update(self, pk: int, data: dict):
        employee = self.get_by_id(pk)
        if employee is None:
            return None
        for field, value in data.items():
            setattr(employee, field, value)
        employee.full_clean()           # Fixed: .update() skipped all validation
        employee.save()
        return employee

    def delete(self, pk: int) -> bool:
        deleted, _ = self.model.objects.filter(pk=pk).delete()
        return deleted > 0

    def email_exists(self, email: str, exclude_id: int = None) -> bool:
        qs = self.model.objects.filter(email__iexact=email)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    def employee_id_exists(self, employee_id: str, exclude_id: int = None) -> bool:
        qs = self.model.objects.filter(employee_id__iexact=employee_id)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    def count(self, **filters) -> int:
        return self.model.objects.filter(**filters).count()

    def count_by_department(self) -> dict:
        # Fixed: group by department name, not the numeric ID
        return dict(
            self.model.objects.values('department__name')
            .annotate(count=Count('id'))
            .values_list('department__name', 'count')
        )

    def list_departments(self):
        from employees.models import Department
        return list(Department.objects.values('id', 'name'))

    def recent(self, limit: int = 5):
        return self.model.objects.select_related('department').order_by('-created_at')[:limit]