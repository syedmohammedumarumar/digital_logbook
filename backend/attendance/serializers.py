# attendance/serializers.py (UPDATED)
# ================================
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import date, time, datetime
from .models import User, AttendanceRecord, SecurityLog, RoleShiftTiming
from .utils import validate_geofence, get_client_ip, get_device_info

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 
                 'role', 'start_date', 'end_date', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate enrollment dates for students and interns
        if data['role'] in ['student', 'intern']:
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError(
                    "Students and interns must have start and end dates"
                )
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError(
                    "Start date must be before end date"
                )
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data

# UPDATED: AttendanceMarkSerializer with notes support
class AttendanceMarkSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, data):
        request = self.context['request']
        user = request.user
        
        # Check enrollment period
        if not user.is_enrollment_active():
            raise serializers.ValidationError(
                "You are not in an active enrollment period"
            )
        
        # Validate geofence
        if not validate_geofence(data['latitude'], data['longitude']):
            # Log security violation
            SecurityLog.objects.create(
                user=user,
                log_type='failed_geo',
                description=f"Geofence validation failed. Location: {data['latitude']}, {data['longitude']}",
                ip_address=get_client_ip(request),
                device_info=get_device_info(request),
                latitude=data['latitude'],
                longitude=data['longitude']
            )
            raise serializers.ValidationError(
                "You must be within office premises to mark attendance"
            )
        
        return data

# UPDATED: AttendanceRecordSerializer with new fields
class AttendanceRecordSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    expected_start_time = serializers.TimeField(read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'user', 'user_name', 'user_role', 'date', 'check_in_time', 
                 'check_out_time', 'is_late', 'notes', 'expected_start_time', 'created_at']
        read_only_fields = ['user', 'created_at']

# NEW: Serializer for updating notes
class AttendanceNotesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ['notes']
    
    def validate_notes(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("Notes cannot exceed 500 characters")
        return value

# NEW: RoleShiftTiming serializer for admin
class RoleShiftTimingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleShiftTiming
        fields = ['id', 'role', 'start_time', 'end_time', 'grace_period_minutes', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    "Start time must be before end time"
                )
        
        if data.get('grace_period_minutes') and data['grace_period_minutes'] < 0:
            raise serializers.ValidationError(
                "Grace period cannot be negative"
            )
        
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'start_date', 'end_date', 'is_active_period', 
                 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']

class UserDateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['start_date', 'end_date', 'is_active_period']
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError(
                    "Start date must be before end date"
                )
        return data

class SecurityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = SecurityLog
        fields = ['id', 'user', 'user_name', 'log_type', 'description', 
                 'ip_address', 'device_info', 'latitude', 'longitude', 'timestamp']