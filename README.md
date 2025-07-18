# Attendance System API Documentation & Postman Testing Guide

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Postman Testing Guide](#postman-testing-guide)
5. [Error Handling](#error-handling)
6. [Security Features](#security-features)

## Overview

This attendance system provides REST API endpoints for user registration, authentication, attendance marking, and administrative functions. The system includes geofencing validation, role-based access control, shift timing management, and comprehensive security logging.

### Base URL
```
http://localhost:8000/api/
```

### Authentication
The API uses JWT (JSON Web Token) authentication with access and refresh tokens.

## API Endpoints

### 1. Authentication Endpoints

#### Register User
**POST** `/register/`

Creates a new user account.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "student",
    "start_date": "2024-01-15",
    "end_date": "2024-12-15",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
}
```

**Validation Rules:**
- Username must be unique
- Email must be valid format
- Password minimum 8 characters
- Students/interns must have start_date and end_date
- start_date must be before end_date

#### Login
**POST** `/login/`

Authenticates user and returns JWT tokens.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student"
    }
}
```

### 2. Attendance Endpoints

#### Mark In
**POST** `/attendance/mark-in/`

Records check-in time and location with shift timing validation.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "latitude": 12.9716,
    "longitude": 77.5946,
    "notes": "Traffic jam on the way" 
}
```

**Response (200 OK):**
```json
{
    "message": "Marked in successfully",
    "time": "2024-01-15T09:30:00Z",
    "is_late": true,
    "expected_start_time": "09:00:00",
    "notes_enabled": true
}
```

**Validation:**
- User must be in active enrollment period
- Location must be within office geofence
- Cannot mark in twice for same date
- Automatic late detection based on role shift timings
- Notes are optional but recommended for late arrivals

#### Mark Out
**POST** `/attendance/mark-out/`

Records check-out time and location.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "latitude": 12.9716,
    "longitude": 77.5946,
    "notes": "Leaving early for appointment"
}
```

**Response (200 OK):**
```json
{
    "message": "Marked out successfully",
    "time": "2024-01-15T18:00:00Z"
}
```

**Validation:**
- Must have marked in before marking out
- Location must be within office geofence
- Cannot mark out twice for same date

#### My Attendance
**GET** `/attendance/my/`

Retrieves current user's attendance records.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_name": "John Doe",
            "user_role": "student",
            "date": "2024-01-15",
            "check_in_time": "2024-01-15T09:30:00Z",
            "check_out_time": "2024-01-15T18:00:00Z",
            "is_late": true,
            "notes": "Traffic jam on the way",
            "expected_start_time": "09:00:00",
            "created_at": "2024-01-15T09:30:00Z"
        }
    ]
}
```

#### **NEW** Update Attendance Notes
**PATCH** `/attendance/<attendance_id>/notes/`

Updates notes for a specific attendance record.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "notes": "Updated reason for being late"
}
```

**Response (200 OK):**
```json
{
    "message": "Notes updated successfully",
    "notes": "Updated reason for being late"
}
```

**Validation:**
- User can only update their own attendance notes
- Can only update notes for today's attendance
- Notes cannot exceed 500 characters

### 3. Admin Endpoints

#### Admin Attendance View
**GET** `/admin/attendance/`

Retrieves all attendance records with filtering options.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `role`: Filter by user role (student, intern, employee, admin)
- `from_date`: Start date filter (YYYY-MM-DD)
- `to_date`: End date filter (YYYY-MM-DD)
- `late_only`: Show only late entries (true/false)

**Example Request:**
```
GET /admin/attendance/?role=student&from_date=2024-01-01&to_date=2024-01-31&late_only=true
```

**Response (200 OK):**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_name": "John Doe",
            "user_role": "student",
            "date": "2024-01-15",
            "check_in_time": "2024-01-15T09:30:00Z",
            "check_out_time": "2024-01-15T18:00:00Z",
            "is_late": true,
            "notes": "Traffic jam on the way",
            "expected_start_time": "09:00:00",
            "created_at": "2024-01-15T09:30:00Z"
        }
    ]
}
```

#### **NEW** Admin Shift Timing Management
**GET** `/admin/shift-timings/`

Retrieves all role-based shift timings.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "role": "student",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "grace_period_minutes": 15,
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        },
        {
            "id": 2,
            "role": "intern",
            "start_time": "09:30:00",
            "end_time": "17:30:00",
            "grace_period_minutes": 10,
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        },
        {
            "id": 3,
            "role": "employee",
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "grace_period_minutes": 15,
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        }
    ]
}
```

#### **NEW** Create Shift Timing
**POST** `/admin/shift-timings/`

Creates a new shift timing for a role.

**Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "role": "student",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "grace_period_minutes": 15
}
```

**Response (201 Created):**
```json
{
    "id": 4,
    "role": "student",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "grace_period_minutes": 15,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
}
```

**Validation:**
- Role must be unique
- start_time must be before end_time
- grace_period_minutes cannot be negative

#### **NEW** Update Shift Timing
**PUT/PATCH** `/admin/shift-timings/<shift_timing_id>/`

Updates an existing shift timing.

**Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "start_time": "08:30:00",
    "end_time": "17:30:00",
    "grace_period_minutes": 20
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "role": "student",
    "start_time": "08:30:00",
    "end_time": "17:30:00",
    "grace_period_minutes": 20,
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
}
```

#### **NEW** Delete Shift Timing
**DELETE** `/admin/shift-timings/<shift_timing_id>/`

Deletes a shift timing configuration.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (204 No Content):**
No response body.

#### **NEW** Get Specific Shift Timing
**GET** `/admin/shift-timings/<shift_timing_id>/`

Retrieves a specific shift timing by ID.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "role": "student",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "grace_period_minutes": 15,
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

#### Admin Users List
**GET** `/admin/users/`

Retrieves all users in the system.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "start_date": "2024-01-15",
            "end_date": "2024-12-15",
            "is_active_period": true,
            "date_joined": "2024-01-10T10:00:00Z",
            "last_login": "2024-01-15T09:00:00Z"
        }
    ]
}
```

#### Update User Dates
**PUT/PATCH** `/admin/user/<user_id>/dates/`

Updates user's enrollment dates and active status.

**Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "start_date": "2024-02-01",
    "end_date": "2024-11-30",
    "is_active_period": true
}
```

**Response (200 OK):**
```json
{
    "start_date": "2024-02-01",
    "end_date": "2024-11-30",
    "is_active_period": true
}
```

#### Export Attendance
**GET** `/admin/export/`

Exports attendance data as CSV file.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `user_id`: Filter by specific user
- `role`: Filter by user role
- `from_date`: Start date filter (YYYY-MM-DD)
- `to_date`: End date filter (YYYY-MM-DD)

**Response:**
Returns CSV file with attendance data including new fields (notes, expected_start_time, late status).

#### Security Logs
**GET** `/admin/security-logs/`

Retrieves security logs for monitoring suspicious activities.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_name": "John Doe",
            "log_type": "failed_geo",
            "description": "Geofence validation failed. Location: 12.9800, 77.6000",
            "ip_address": "192.168.1.100",
            "device_info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "latitude": "12.9800",
            "longitude": "77.6000",
            "timestamp": "2024-01-15T09:25:00Z"
        }
    ]
}
```

## Postman Testing Guide

### 1. Setup Collection

1. Create a new Postman collection named "Attendance System API"
2. Add the base URL as a collection variable: `baseUrl = http://localhost:8000/api`

### 2. Environment Variables

Create environment variables:
- `baseUrl`: http://localhost:8000/api
- `accessToken`: (will be set after login)
- `refreshToken`: (will be set after login)
- `adminAccessToken`: (will be set after admin login)
- `attendanceId`: (will be set after creating attendance)
- `shiftTimingId`: (will be set after creating shift timing)

### 3. Test Scenarios

#### Scenario 1: User Registration and Login

**Step 1: Register Student**
```
POST {{baseUrl}}/register/
Content-Type: application/json

{
    "username": "student_test",
    "email": "student@test.com",
    "first_name": "Test",
    "last_name": "Student",
    "phone": "+1234567890",
    "role": "student",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "password": "password123",
    "password_confirm": "password123"
}
```

**Step 2: Login Student**
```
POST {{baseUrl}}/login/
Content-Type: application/json

{
    "username": "student_test",
    "password": "password123"
}
```

**Test Script (Tests tab):**
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('access');
    pm.expect(responseJson).to.have.property('refresh');
    
    // Set tokens as environment variables
    pm.environment.set("accessToken", responseJson.access);
    pm.environment.set("refreshToken", responseJson.refresh);
});
```

#### Scenario 2: Attendance Marking with Notes

**Step 1: Mark In (Late with Notes)**
```
POST {{baseUrl}}/attendance/mark-in/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
    "latitude": 12.9716,
    "longitude": 77.5946,
    "notes": "Traffic jam on the way to office"
}
```

**Test Script:**
```javascript
pm.test("Mark in successful", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson.message).to.equal("Marked in successfully");
    pm.expect(responseJson).to.have.property('time');
    pm.expect(responseJson).to.have.property('is_late');
    pm.expect(responseJson).to.have.property('expected_start_time');
    pm.expect(responseJson).to.have.property('notes_enabled');
});
```

**Step 2: Update Attendance Notes**
```
PATCH {{baseUrl}}/attendance/{{attendanceId}}/notes/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
    "notes": "Updated: Heavy traffic due to road construction"
}
```

**Test Script:**
```javascript
pm.test("Notes updated successfully", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson.message).to.equal("Notes updated successfully");
    pm.expect(responseJson).to.have.property('notes');
});
```

**Step 3: Mark Out**
```
POST {{baseUrl}}/attendance/mark-out/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
    "latitude": 12.9716,
    "longitude": 77.5946,
    "notes": "Leaving on time today"
}
```

**Step 4: View My Attendance**
```
GET {{baseUrl}}/attendance/my/
Authorization: Bearer {{accessToken}}
```

**Test Script:**
```javascript
pm.test("My attendance retrieved", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('results');
    pm.expect(responseJson.results).to.be.an('array');
    
    if (responseJson.results.length > 0) {
        pm.environment.set("attendanceId", responseJson.results[0].id);
    }
});
```

#### Scenario 3: Admin Operations

**Step 1: Register Admin**
```
POST {{baseUrl}}/register/
Content-Type: application/json

{
    "username": "admin_test",
    "email": "admin@test.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "password": "adminpass123",
    "password_confirm": "adminpass123"
}
```

**Step 2: Login Admin**
```
POST {{baseUrl}}/login/
Content-Type: application/json

{
    "username": "admin_test",
    "password": "adminpass123"
}
```

**Test Script:**
```javascript
pm.test("Admin login successful", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.environment.set("adminAccessToken", responseJson.access);
});
```

#### **NEW** Scenario 4: Shift Timing Management

**Step 1: Get All Shift Timings**
```
GET {{baseUrl}}/admin/shift-timings/
Authorization: Bearer {{adminAccessToken}}
```

**Test Script:**
```javascript
pm.test("Shift timings retrieved", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('results');
    pm.expect(responseJson.results).to.be.an('array');
    
    if (responseJson.results.length > 0) {
        pm.environment.set("shiftTimingId", responseJson.results[0].id);
    }
});
```

**Step 2: Create New Shift Timing**
```
POST {{baseUrl}}/admin/shift-timings/
Authorization: Bearer {{adminAccessToken}}
Content-Type: application/json

{
    "role": "student",
    "start_time": "08:30:00",
    "end_time": "16:30:00",
    "grace_period_minutes": 20
}
```

**Test Script:**
```javascript
pm.test("Shift timing created", function () {
    pm.response.to.have.status(201);
    var responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('id');
    pm.expect(responseJson.role).to.equal('student');
    pm.environment.set("shiftTimingId", responseJson.id);
});
```

**Step 3: Update Shift Timing**
```
PATCH {{baseUrl}}/admin/shift-timings/{{shiftTimingId}}/
Authorization: Bearer {{adminAccessToken}}
Content-Type: application/json

{
    "start_time": "09:00:00",
    "grace_period_minutes": 15
}
```

**Test Script:**
```javascript
pm.test("Shift timing updated", function () {
    pm.response.to.have.status(200);
    var responseJson = pm.response.json();
    pm.expect(responseJson.start_time).to.equal('09:00:00');
    pm.expect(responseJson.grace_period_minutes).to.equal(15);
});
```

**Step 4: Get Specific Shift Timing**
```
GET {{baseUrl}}/admin/shift-timings/{{shiftTimingId}}/
Authorization: Bearer {{adminAccessToken}}
```

**Step 5: Delete Shift Timing**
```
DELETE {{baseUrl}}/admin/shift-timings/{{shiftTimingId}}/
Authorization: Bearer {{adminAccessToken}}
```

**Test Script:**
```javascript
pm.test("Shift timing deleted", function () {
    pm.response.to.have.status(204);
});
```

#### Scenario 5: Enhanced Admin Attendance View

**Step 1: View All Attendance with New Fields**
```
GET {{baseUrl}}/admin/attendance/
Authorization: Bearer {{adminAccessToken}}
```

**Step 2: Filter Late Attendees**
```
GET {{baseUrl}}/admin/attendance/?late_only=true
Authorization: Bearer {{adminAccessToken}}
```

**Step 3: Filter by Role and Date Range**
```
GET {{baseUrl}}/admin/attendance/?role=student&from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer {{adminAccessToken}}
```

**Step 4: Export Attendance with New Fields**
```
GET {{baseUrl}}/admin/export/?from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer {{adminAccessToken}}
```

### 4. Error Testing

#### Test Invalid Shift Timing
```
POST {{baseUrl}}/admin/shift-timings/
Authorization: Bearer {{adminAccessToken}}
Content-Type: application/json

{
    "role": "student",
    "start_time": "18:00:00",
    "end_time": "09:00:00",
    "grace_period_minutes": -5
}
```

**Expected Response (400 Bad Request):**
```json
{
    "non_field_errors": ["Start time must be before end time"],
    "grace_period_minutes": ["Grace period cannot be negative"]
}
```

#### Test Update Notes for Non-Existent Attendance
```
PATCH {{baseUrl}}/attendance/999/notes/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
    "notes": "This should fail"
}
```

**Expected Response (404 Not Found):**
```json
{
    "error": "Attendance record not found"
}
```

#### Test Update Notes for Other User's Attendance
```
PATCH {{baseUrl}}/attendance/{{attendanceId}}/notes/
Authorization: Bearer {{otherUserAccessToken}}
Content-Type: application/json

{
    "notes": "Trying to update someone else's attendance"
}
```

**Expected Response (403 Forbidden):**
```json
{
    "error": "You can only update your own attendance notes"
}
```

### 5. Collection-Level Tests

Add these tests to your collection:

```javascript
pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(3000);
});

pm.test("Response has correct content type", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});

pm.test("No server errors", function () {
    pm.expect(pm.response.code).to.be.below(500);
});
```

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid input data or validation errors
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### New Error Scenarios

#### Shift Timing Errors
```json
{
    "non_field_errors": ["Start time must be before end time"],
    "grace_period_minutes": ["Grace period cannot be negative"]
}
```

#### Notes Update Errors
```json
{
    "error": "You can only update your own attendance notes"
}
```

```json
{
    "error": "You can only update notes for today's attendance"
}
```

```json
{
    "notes": ["Notes cannot exceed 500 characters"]
}
```

## Security Features

### 1. Enhanced Late Detection
- Automatic late detection based on role-specific shift timings
- Configurable grace periods per role
- Expected start time tracking

### 2. Notes Management
- Secure notes updating with ownership validation
- Time-based restrictions for note updates
- Character limit enforcement

### 3. Shift Timing Security
- Admin-only access to shift timing management
- Validation of timing constraints
- Audit trail for timing changes

## Testing Checklist

**Basic Features:**
- [ ] User registration with all roles
- [ ] User login and token generation
- [ ] Attendance marking (in/out)
- [ ] Geofence validation
- [ ] Duplicate attendance prevention
- [ ] Enrollment period validation

**New Features:**
- [ ] Attendance marking with notes
- [ ] Update attendance notes
- [ ] Late detection with shift timings
- [ ] Create shift timing
- [ ] Update shift timing
- [ ] Delete shift timing
- [ ] Get all shift timings
- [ ] Get specific shift timing

**Admin Features:**
- [ ] Admin attendance filtering with new fields
- [ ] User date updates
- [ ] CSV export with new fields
- [ ] Security log monitoring
- [ ] Shift timing management

**Error Handling:**
- [ ] Invalid shift timing validation
- [ ] Notes update permission checks
- [ ] Time-based restrictions
- [ ] Character limit enforcement
- [ ] Duplicate shift timing prevention

**Security:**
- [ ] Role-based access control
- [ ] Ownership validation for notes
- [ ] Admin-only shift timing access
- [ ] Audit trail verification

## Additional Notes

### Default Shift Timings
The system creates default shift timings for roles:
- **Student**: 9:00 AM - 5:00 PM (15 min grace period)
- **Intern**: 9:30 AM - 5:30 PM (10 min grace period)
- **Employee**: 9:00 AM - 6:00 PM (15 min grace period)

### Notes Feature
- Notes are optional for attendance marking
- Recommended for late arrivals
- Can be updated only by the attendance owner
- Limited to today's attendance records
- Maximum 500 characters

### Late Detection Logic
- Based on role-specific shift timings
- Grace period is added to start time
- Check-in after grace period end time is marked as late
- Expected start time is stored for reference