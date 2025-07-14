# attendance/utils.py
import math
import csv
import io
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime, date, time

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_device_info(request):
    """Get device information from request"""
    return {
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    # Convert all to float to prevent float-Decimal errors
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def validate_geofence(latitude, longitude):
    """Validate if coordinates are within office geofence"""
    office_lat = settings.OFFICE_LOCATION['latitude']
    office_lon = settings.OFFICE_LOCATION['longitude']
    allowed_radius = settings.OFFICE_LOCATION['radius']
    
    distance = calculate_distance(latitude, longitude, office_lat, office_lon)
    return distance <= float(allowed_radius)  # Ensure this comparison works

def generate_attendance_csv(attendance_records):
    """Generate CSV file from attendance records"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Name', 'Role', 'Date', 'Check In', 'Check Out', 'Late', 'Notes'
    ])
    
    # Write data
    for record in attendance_records:
        writer.writerow([
            record.user.get_full_name(),
            record.user.get_role_display(),
            record.date.strftime('%Y-%m-%d'),
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '',
            'Yes' if record.is_late else 'No',
            record.notes
        ])
    
    output.seek(0)
    return output.getvalue()

def create_csv_response(csv_content, filename):
    """Create HTTP response with CSV content"""
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
