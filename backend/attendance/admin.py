# attendance/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AttendanceRecord, SecurityLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'start_date', 'end_date', 'is_active_period')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'start_date', 'end_date', 'is_active_period')
        }),
    )
    list_display = ('username', 'email', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('role', 'is_active', 'start_date', 'end_date')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in_time', 'check_out_time', 'is_late')
    list_filter = ('date', 'is_late', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('check_in_ip', 'check_out_ip', 'check_in_device_info', 'check_out_device_info')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_type', 'timestamp', 'ip_address')
    list_filter = ('log_type', 'timestamp', 'user__role')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')