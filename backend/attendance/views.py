# attendance/views.py (UPDATED)
# ================================
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q
from datetime import date, datetime, time
from .models import User, AttendanceRecord, SecurityLog, RoleShiftTiming
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, AttendanceMarkSerializer,
    AttendanceRecordSerializer, UserSerializer, UserDateUpdateSerializer,
    SecurityLogSerializer, AttendanceNotesUpdateSerializer, RoleShiftTimingSerializer
)
from .permissions import IsAdminUser, IsOwnerOrAdmin
from .utils import get_client_ip, get_device_info, generate_attendance_csv, create_csv_response

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# UPDATED: mark_in_view with shift timing validation
@api_view(['POST'])
def mark_in_view(request):
    serializer = AttendanceMarkSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        today = date.today()
        
        # Check if already marked in today
        record, created = AttendanceRecord.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'check_in_time': timezone.now(),
                'check_in_latitude': serializer.validated_data['latitude'],
                'check_in_longitude': serializer.validated_data['longitude'],
                'check_in_ip': get_client_ip(request),
                'check_in_device_info': str(get_device_info(request)),
                'notes': serializer.validated_data.get('notes', ''),
            }
        )
        
        if not created and record.check_in_time:
            # Log duplicate attempt
            SecurityLog.objects.create(
                user=user,
                log_type='duplicate_attempt',
                description=f"Duplicate check-in attempt for {today}",
                ip_address=get_client_ip(request),
                device_info=str(get_device_info(request)),
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude']
            )
            return Response(
                {'error': 'You have already marked in for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not created:
            # Update existing record with check-in data
            record.check_in_time = timezone.now()
            record.check_in_latitude = serializer.validated_data['latitude']
            record.check_in_longitude = serializer.validated_data['longitude']
            record.check_in_ip = get_client_ip(request)
            record.check_in_device_info = str(get_device_info(request))
            record.notes = serializer.validated_data.get('notes', '')
            record.save()
        
        # Get shift timing and prepare response
        response_data = {
            'message': 'Marked in successfully',
            'time': record.check_in_time,
            'is_late': record.is_late,
            'notes_enabled': record.is_late,  # Enable notes only if late
        }
        
        # Add expected start time if role has shift timing
        if record.expected_start_time:
            response_data['expected_start_time'] = record.expected_start_time
        
        return Response(response_data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def mark_out_view(request):
    serializer = AttendanceMarkSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        today = date.today()
        
        try:
            record = AttendanceRecord.objects.get(user=user, date=today)
        except AttendanceRecord.DoesNotExist:
            return Response(
                {'error': 'You must mark in before marking out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not record.check_in_time:
            return Response(
                {'error': 'You must mark in before marking out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if record.check_out_time:
            # Log duplicate attempt
            SecurityLog.objects.create(
                user=user,
                log_type='duplicate_attempt',
                description=f"Duplicate check-out attempt for {today}",
                ip_address=get_client_ip(request),
                device_info=str(get_device_info(request)),
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude']
            )
            return Response(
                {'error': 'You have already marked out for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update record with check-out data
        record.check_out_time = timezone.now()
        record.check_out_latitude = serializer.validated_data['latitude']
        record.check_out_longitude = serializer.validated_data['longitude']
        record.check_out_ip = get_client_ip(request)
        record.check_out_device_info = str(get_device_info(request))
        record.save()
        
        return Response({
            'message': 'Marked out successfully',
            'time': record.check_out_time
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# NEW: Update attendance notes endpoint
@api_view(['PATCH'])
def update_attendance_notes(request, attendance_id):
    try:
        attendance = AttendanceRecord.objects.get(id=attendance_id)
    except AttendanceRecord.DoesNotExist:
        return Response(
            {'error': 'Attendance record not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions - user can only update their own attendance
    if attendance.user != request.user:
        return Response(
            {'error': 'You can only update your own attendance notes'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if attendance is from today (optional restriction)
    if attendance.date != date.today():
        return Response(
            {'error': 'You can only update notes for today\'s attendance'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = AttendanceNotesUpdateSerializer(
        attendance, 
        data=request.data, 
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Notes updated successfully',
            'notes': serializer.validated_data['notes']
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AttendanceRecord.objects.filter(user=self.request.user)

class AdminAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = AttendanceRecord.objects.all()
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(user__role=role)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=from_date)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=to_date)
            except ValueError:
                pass
        
        # Filter latecomers
        late_only = self.request.query_params.get('late_only')
        if late_only and late_only.lower() == 'true':
            queryset = queryset.filter(is_late=True)
        
        return queryset.select_related('user')

# NEW: Admin shift timing management
class AdminShiftTimingListView(generics.ListCreateAPIView):
    serializer_class = RoleShiftTimingSerializer
    permission_classes = [IsAdminUser]
    queryset = RoleShiftTiming.objects.all()

class AdminShiftTimingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoleShiftTimingSerializer
    permission_classes = [IsAdminUser]
    queryset = RoleShiftTiming.objects.all()

class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return User.objects.all().order_by('username')

class AdminUserUpdateView(generics.UpdateAPIView):
    serializer_class = UserDateUpdateSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return User.objects.all()

@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_attendance_view(request):
    # Get filter parameters
    user_id = request.query_params.get('user_id')
    role = request.query_params.get('role')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')
    
    # Build queryset
    queryset = AttendanceRecord.objects.all()
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if role:
        queryset = queryset.filter(user__role=role)
    
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=from_date)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__lte=to_date)
        except ValueError:
            pass
    
    # Generate CSV
    records = queryset.select_related('user').order_by('date', 'user__username')
    csv_content = generate_attendance_csv(records)
    
    # Create filename
    filename = f"attendance_report_{date.today().strftime('%Y%m%d')}.csv"
    
    return create_csv_response(csv_content, filename)

class SecurityLogView(generics.ListAPIView):
    serializer_class = SecurityLogSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return SecurityLog.objects.all().select_related('user')