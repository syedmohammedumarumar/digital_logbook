# attendance/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta
from .models import AttendanceRecord, SecurityLog
from .utils import validate_geofence, calculate_distance

User = get_user_model()

class UserModelTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=25)
        )
        
        self.employee = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123',
            role='employee'
        )
    
    def test_student_enrollment_active(self):
        """Test that student enrollment is active within dates"""
        self.assertTrue(self.student.is_enrollment_active())
    
    def test_student_enrollment_inactive_before_start(self):
        """Test that student enrollment is inactive before start date"""
        past_date = self.student.start_date - timedelta(days=1)
        self.assertFalse(self.student.is_enrollment_active(past_date))
    
    def test_student_enrollment_inactive_after_end(self):
        """Test that student enrollment is inactive after end date"""
        future_date = self.student.end_date + timedelta(days=1)
        self.assertFalse(self.student.is_enrollment_active(future_date))
    
    def test_employee_always_active(self):
        """Test that employee is always active"""
        self.assertTrue(self.employee.is_enrollment_active())

class GeofenceTestCase(TestCase):
    def test_valid_location(self):
        """Test that office location is valid"""
        office_lat = 17.4375
        office_lon = 78.4483
        self.assertTrue(validate_geofence(office_lat, office_lon))
    
    def test_invalid_location(self):
        """Test that location outside office is invalid"""
        # Far away location
        self.assertFalse(validate_geofence(17.5000, 78.5000))
    
    def test_distance_calculation(self):
        """Test distance calculation function"""
        # Distance between two same points should be 0
        distance = calculate_distance(17.4375, 78.4483, 17.4375, 78.4483)
        self.assertEqual(distance, 0)
        
        # Distance should be positive
        distance = calculate_distance(17.4375, 78.4483, 17.4376, 78.4484)
        self.assertGreater(distance, 0)

class AttendanceAPITestCase(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=25)
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Get tokens
        self.student_token = RefreshToken.for_user(self.student).access_token
        self.admin_token = RefreshToken.for_user(self.admin).access_token
    
    def test_user_registration(self):
        """Test user registration"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'student',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_user_login(self):
        """Test user login"""
        url = reverse('login')
        data = {
            'username': 'student1',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_mark_in_success(self):
        """Test successful mark in"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = reverse('mark_in')
        data = {
            'latitude': 17.4375,
            'longitude': 78.4483
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Check record was created
        self.assertTrue(
            AttendanceRecord.objects.filter(
                user=self.student,
                date=date.today()
            ).exists()
        )
    
    def test_mark_in_invalid_location(self):
        """Test mark in with invalid location"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = reverse('mark_in')
        data = {
            'latitude': 17.5000,
            'longitude': 78.5000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check security log was created
        self.assertTrue(
            SecurityLog.objects.filter(
                user=self.student,
                log_type='failed_geo'
            ).exists()
        )
    
    def test_mark_out_without_mark_in(self):
        """Test mark out without mark in"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = reverse('mark_out')
        data = {
            'latitude': 17.4375,
            'longitude': 78.4483
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_attendance_view(self):
        """Test admin attendance view"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        url = reverse('admin_attendance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_admin_cannot_access_admin_views(self):
        """Test that non-admin cannot access admin views"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = reverse('admin_attendance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
