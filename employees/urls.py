from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.hello, name='hello'),
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee-add'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee-edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee-delete'),
]