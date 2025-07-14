# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    
    # Attendance
    path('attendance/mark-in/', views.mark_in_view, name='mark_in'),
    path('attendance/mark-out/', views.mark_out_view, name='mark_out'),
    path('attendance/my/', views.MyAttendanceView.as_view(), name='my_attendance'),
    
    # Admin endpoints
    path('admin/attendance/', views.AdminAttendanceView.as_view(), name='admin_attendance'),
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/user/<int:pk>/dates/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/export/', views.export_attendance_view, name='export_attendance'),
    path('admin/security-logs/', views.SecurityLogView.as_view(), name='security_logs'),
]