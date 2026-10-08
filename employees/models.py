from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator 
from django.utils import timezone 

# Create your models here.
def validate_not_future(value):
    """Reject hire dates that are in the future."""
    if value > timezone.localdate():
        raise ValidationError("Hire date cannot be in the future.")


phone_validator = RegexValidator(
    regex=r'^\+?[0-9\s\-]{7,15}$',
    message="Enter a valid phone number (7-15 digits, may start with +).",
)


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on_leave', 'On Leave'
        TERMINATED = 'terminated', 'Terminated'

    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=20, blank=True, validators=[phone_validator]
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    job_title = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=50)
    hire_date = models.DateField(validators=[validate_not_future])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        if self.status == self.Status.TERMINATED and self.is_active:
            raise ValidationError("A terminated employee cannot be marked as active.")

