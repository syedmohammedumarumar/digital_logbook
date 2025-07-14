# attendance/models.py (ADD THIS NEW MODEL)
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date, time, datetime
import json

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('intern', 'Intern'),
        ('employee', 'Employee'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active_period = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_enrollment_active(self, check_date=None):
        """Check if user's enrollment period is active"""
        if check_date is None:
            check_date = date.today()
        
        # Employees and admins don't have enrollment periods
        if self.role in ['employee', 'admin']:
            return True
        
        # Students and interns must have start/end dates
        if not self.start_date or not self.end_date:
            return False
        
        return self.start_date <= check_date <= self.end_date and self.is_active_period

# NEW MODEL: Role-based shift timings
class RoleShiftTiming(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('intern', 'Intern'),
        ('employee', 'Employee'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    start_time = models.TimeField(default=time(9, 0))  # 9:00 AM
    end_time = models.TimeField(default=time(18, 0))   # 6:00 PM
    grace_period_minutes = models.IntegerField(default=15)  # 15 minutes grace period
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['role']
    
    def __str__(self):
        return f"{self.get_role_display()} - {self.start_time} to {self.end_time}"
    
    @classmethod
    def get_shift_timing(cls, role):
        """Get shift timing for a specific role, create default if not exists"""
        timing, created = cls.objects.get_or_create(
            role=role,
            defaults={
                'start_time': time(9, 0),
                'end_time': time(18, 0),
                'grace_period_minutes': 15
            }
        )
        return timing

class AttendanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    
    # Check-in information
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    check_in_ip = models.GenericIPAddressField(null=True, blank=True)
    check_in_device_info = models.TextField(null=True, blank=True)
    
    # Check-out information
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    check_out_ip = models.GenericIPAddressField(null=True, blank=True)
    check_out_device_info = models.TextField(null=True, blank=True)
    
    # Status tracking
    is_late = models.BooleanField(default=False)
    notes = models.TextField(blank=True)  # For late notes
    expected_start_time = models.TimeField(null=True, blank=True)  # Expected start time from shift
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Check if check-in is late based on role shift timing
        if self.check_in_time and self.user.role in ['student', 'intern', 'employee']:
            shift_timing = RoleShiftTiming.get_shift_timing(self.user.role)
            self.expected_start_time = shift_timing.start_time
            
            # Calculate grace period end time
            grace_period_end = datetime.combine(
                self.date, 
                shift_timing.start_time
            ) + timezone.timedelta(minutes=shift_timing.grace_period_minutes)
            
            # Check if late (after grace period)
            check_in_datetime = self.check_in_time
            if timezone.is_naive(check_in_datetime):
                check_in_datetime = timezone.make_aware(check_in_datetime)
            
            self.is_late = check_in_datetime.time() > grace_period_end.time()
        
        super().save(*args, **kwargs)

class SecurityLog(models.Model):
    LOG_TYPES = [
        ('failed_geo', 'Failed Geo-fence Validation'),
        ('duplicate_attempt', 'Duplicate Attendance Attempt'),
        ('invalid_period', 'Invalid Enrollment Period'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    device_info = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.log_type} - {self.timestamp}"