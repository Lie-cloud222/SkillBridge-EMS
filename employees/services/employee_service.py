import logging
logger = logging.getLogger(__name__)
from typing import List, Optional 
from django.core.cache import cache 
from employees.repositories.employee_repository import EmployeeRepository 
 
 
class EmployeeService:  
    CACHE_KEY_STATS = 'employees:stats' 
    CACHE_TIMEOUT = 300 
    CACHE_KEY_DEPARTMENTS = 'departments:all'

    def get_departments(self) -> list:
        departments = cache.get(self.CACHE_KEY_DEPARTMENTS)
        if departments is None:
            departments = self.repository.list_departments()
            cache.set(self.CACHE_KEY_DEPARTMENTS, departments, self.CACHE_TIMEOUT)
        return departments

    def recent_employees(self, limit: int = 5):
        return self.repository.recent(limit)
 
    def __init__(self, repository: EmployeeRepository = None): 
        self.repository = repository or EmployeeRepository() 

    def list_employees(self, query: str = None, department: int = None, status: str =None):
        return self.repository.search_and_filter(query, department, status)
 
    def get_employee_by_id(self, pk: int) -> Optional: 
        return self.repository.get_by_id(pk) 
 
    def search_employees(self, query: str) -> List: 
        if not query or len(query) < 2: 
            return self.get_all_employees() 
        return list(self.repository.search(query)) 
 
    def filter_employees(self, department: str = None, is_active: bool = None) -> List: 
        return list(self.repository.filter(department=department, is_active=is_active)) 
 
    def create_employee(self, data: dict):
        if self.repository.email_exists(data.get('email')):
            logger.warning("Create rejected: duplicate email %s", data.get('email'))
            raise ValueError("An employee with this email already exists.")
        if self.repository.employee_id_exists(data.get('employee_id')):
            logger.warning("Create rejected: duplicate employee ID %s", data.get('employee_id'))
            raise ValueError("This employee ID is already in use.")
        employee = self.repository.create(data)
        self._invalidate_cache()
        logger.info("Employee created: %s", employee)
        return employee
 
    def update_employee(self, pk: int, data: dict):
        if not self.repository.get_by_id(pk):
            logger.warning("Update rejected: employee id=%s not found", pk)
            raise ValueError(f"Employee with ID {pk} not found.")
        new_email = data.get('email')
        if new_email and self.repository.email_exists(new_email, exclude_id=pk):
            logger.warning("Update rejected: duplicate email %s", new_email)
            raise ValueError("An employee with this email already exists.")
        new_emp_id = data.get('employee_id')
        if new_emp_id and self.repository.employee_id_exists(new_emp_id, exclude_id=pk):
            logger.warning("Update rejected: duplicate employee ID %s", new_emp_id)
            raise ValueError("This employee ID is already in use.")
        updated = self.repository.update(pk, data)
        self._invalidate_cache()
        logger.info("Employee updated: id=%s", pk)
        return updated
 
    def delete_employee(self, pk: int) -> bool:
        result = self.repository.delete(pk)
        self._invalidate_cache()
        logger.warning("Employee deleted: id=%s (success=%s)", pk, result)
        return result
 
    def get_statistics(self) -> dict: 
        cached = cache.get(self.CACHE_KEY_STATS) 
        if cached is not None: 
            return cached 
        stats = { 
            'total': self.repository.count(), 
            'active': self.repository.count(is_active=True), 
            'inactive': self.repository.count(is_active=False), 
            'by_department': self.repository.count_by_department(), 
        } 
        cache.set(self.CACHE_KEY_STATS, stats, self.CACHE_TIMEOUT) 
        return stats 

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
 
    def _invalidate_cache(self): 
        cache.delete(self.CACHE_KEY_STATS) 