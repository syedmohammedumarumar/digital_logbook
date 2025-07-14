# attendance/management/commands/generate_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, datetime, time
import random
from attendance.models import AttendanceRecord

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test data for attendance system'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to generate data for')
        parser.add_argument('--users', type=int, default=10, help='Number of test users to create')

    def handle(self, *args, **options):
        days = options['days']
        user_count = options['users']
        
        # Create test users
        roles = ['student', 'intern', 'employee']
        for i in range(user_count):
            role = random.choice(roles)
            start_date = date.today() - timedelta(days=45)
            end_date = start_date + timedelta(days=60)
            
            if role == 'employee':
                start_date = None
                end_date = None
            
            user, created = User.objects.get_or_create(
                username=f'user{i+1}',
                defaults={
                    'email': f'user{i+1}@example.com',
                    'first_name': f'User',
                    'last_name': f'{i+1}',
                    'role': role,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active_period': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username} ({role})')
        
        # Generate attendance records
        users = User.objects.filter(role__in=['student', 'intern', 'employee'])
        start_date = date.today() - timedelta(days=days)
        
        for single_date in (start_date + timedelta(n) for n in range(days)):
            # Skip weekends
            if single_date.weekday() >= 5:
                continue
            
            for user in users:
                # Check if user is in active period
                if not user.is_enrollment_active(single_date):
                    continue
                
                # 85% chance of attendance
                if random.random() < 0.85:
                    # Random check-in time between 8:30 AM and 10:00 AM
                    check_in_hour = random.randint(8, 9)
                    check_in_minute = random.randint(0, 59)
                    
                    if check_in_hour == 9 and check_in_minute > 30:
                        check_in_hour = 10
                        check_in_minute = random.randint(0, 30)
                    
                    check_in_time = datetime.combine(
                        single_date,
                        time(check_in_hour, check_in_minute)
                    )
                    check_in_time = timezone.make_aware(check_in_time)
                    
                    # Random check-out time between 5:00 PM and 7:00 PM
                    check_out_hour = random.randint(17, 18)
                    check_out_minute = random.randint(0, 59)
                    
                    if check_out_hour == 18 and check_out_minute > 30:
                        check_out_hour = 19
                        check_out_minute = random.randint(0, 30)
                    
                    check_out_time = datetime.combine(
                        single_date,
                        time(check_out_hour, check_out_minute)
                    )
                    check_out_time = timezone.make_aware(check_out_time)
                    
                    # Office location with slight variation
                    office_lat = 17.4375
                    office_lon = 78.4483
                    lat_variation = random.uniform(-0.0001, 0.0001)
                    lon_variation = random.uniform(-0.0001, 0.0001)
                    
                    record, created = AttendanceRecord.objects.get_or_create(
                        user=user,
                        date=single_date,
                        defaults={
                            'check_in_time': check_in_time,
                            'check_in_latitude': office_lat + lat_variation,
                            'check_in_longitude': office_lon + lon_variation,
                            'check_in_ip': f'192.168.1.{random.randint(1, 254)}',
                            'check_in_device_info': 'Test Device Info',
                            'check_out_time': check_out_time,
                            'check_out_latitude': office_lat + lat_variation,
                            'check_out_longitude': office_lon + lon_variation,
                            'check_out_ip': f'192.168.1.{random.randint(1, 254)}',
                            'check_out_device_info': 'Test Device Info',
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'Created attendance for {user.username} on {single_date}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated test data for {days} days')
        )