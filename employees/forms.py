from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'department',
            'job_title',
            'employment_type',
            'hire_date',
            'salary',
            'status',
            'is_active',
        ]

        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'salary': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for name, field in self.fields.items():
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'

        def clean_employee_id(self):
            return self.cleaned_data['employee_id'].strip().upper()

        def clean_email(self):
            email = self.cleaned_data['email'].strip().lower()
            duplicates = Employee.objects.filter(email=email)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError("An employee with this email already exists.")
            return email
        
        def clean_first_name(self):
            return self.cleaned_date['first_name'].strip().title()
        
        def clean_last_name(self):
            return self.cleaned_data['last_name'].strip().title()


             