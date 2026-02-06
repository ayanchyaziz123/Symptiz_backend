# ==================== users/urls.py (WITH OTP ENDPOINTS) ====================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    VerifyOTPView,
    ResendOTPView,
    LoginView,
    LoginWithOTPView,
    RequestPasswordResetView,
    ResetPasswordView,
    LogoutView,
    ProfilePictureUploadView,
    InsuranceDocumentUploadView,
    UserProfileView,
    ChangePasswordView,
)

# Create router for viewsets
router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')
# router.register(r'patients', PatientViewSet, basename='patient')

urlpatterns = [
    # ===== OTP-BASED AUTHENTICATION =====
    
    # Registration with OTP
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Login options
    path('auth/login/', LoginView.as_view(), name='login'),  # Traditional login
    path('auth/login-with-otp/', LoginWithOTPView.as_view(), name='login-with-otp'),  # OTP login
    
    # Password reset with OTP
    path('auth/request-password-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    
    # Logout
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Profile Picture
    path('profile/picture/', ProfilePictureUploadView.as_view(), name='profile-picture'),

    # Insurance Document
    path('insurance/document/', InsuranceDocumentUploadView.as_view(), name='insurance-document'),

    # User Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Change Password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Include router URLs
    path('', include(router.urls)),
]


# ====================================================================================
# OTP AUTHENTICATION FLOW DOCUMENTATION
# ====================================================================================

"""
==========================================
REGISTRATION FLOW (WITH EMAIL OTP)
==========================================

Step 1: Register User
---------------------
POST /api/users/auth/register/
Content-Type: application/json

Body:
{
    "username": "john_patient",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "patient",
    "phone": "555-1234"
}

Response (201 Created):
{
    "message": "Registration successful. Please check your email for OTP.",
    "user_id": 1,
    "email": "john@example.com",
    "otp_expires_in_minutes": 10,
    "next_step": "Verify OTP at /api/users/auth/verify-otp/"
}

Note: User receives an email with 6-digit OTP valid for 10 minutes.


Step 2: Verify Email with OTP
------------------------------
POST /api/users/auth/verify-otp/
Content-Type: application/json

Body:
{
    "email": "john@example.com",
    "otp": "123456",
    "purpose": "registration"
}

Response (200 OK):
{
    "message": "OTP verified successfully",
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "john_patient",
    "email": "john@example.com",
    "user_type": "patient",
    "is_email_verified": true
}

Note: 
- User's email is now verified
- Authentication token is provided
- User receives a welcome email
- Can now use all features


Step 3: Resend OTP (if needed)
-------------------------------
POST /api/users/auth/resend-otp/
Content-Type: application/json

Body:
{
    "email": "john@example.com",
    "purpose": "registration"
}

Response (200 OK):
{
    "message": "OTP sent successfully. Please check your email.",
    "email": "john@example.com",
    "otp_expires_in_minutes": 10
}

Note: Maximum 3 OTP requests per 30 minutes


==========================================
LOGIN FLOWS
==========================================

Option 1: Traditional Login (Password-based)
---------------------------------------------
POST /api/users/auth/login/
Content-Type: application/json

Body:
{
    "username": "john_patient",  // or "email": "john@example.com"
    "password": "SecurePass123!"
}

Response (200 OK):
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "john_patient",
    "email": "john@example.com",
    "user_type": "patient",
    "first_name": "John",
    "last_name": "Doe",
    "is_email_verified": true,
    "message": "Login successful"
}

Note: Requires email to be verified


Option 2: Login with OTP (Passwordless)
----------------------------------------
Step 1: Request OTP
POST /api/users/auth/login-with-otp/
Content-Type: application/json

Body:
{
    "email": "john@example.com"
}

Response (200 OK):
{
    "message": "OTP sent successfully. Please check your email.",
    "email": "john@example.com",
    "otp_expires_in_minutes": 10,
    "next_step": "Verify OTP at /api/users/auth/verify-otp/ with purpose=login"
}

Step 2: Verify OTP
POST /api/users/auth/verify-otp/
Content-Type: application/json

Body:
{
    "email": "john@example.com",
    "otp": "123456",
    "purpose": "login"
}

Response (200 OK):
{
    "message": "OTP verified successfully",
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "john_patient",
    "email": "john@example.com",
    "user_type": "patient",
    "is_email_verified": true
}


==========================================
PASSWORD RESET FLOW (WITH OTP)
==========================================

Step 1: Request Password Reset OTP
-----------------------------------
POST /api/users/auth/request-password-reset/
Content-Type: application/json

Body:
{
    "email": "john@example.com"
}

Response (200 OK):
{
    "message": "If an account exists with this email, you will receive a password reset OTP.",
    "next_step": "Use OTP to reset password at /api/users/auth/reset-password/"
}

Note: User receives OTP email


Step 2: Reset Password with OTP
--------------------------------
POST /api/users/auth/reset-password/
Content-Type: application/json

Body:
{
    "email": "john@example.com",
    "otp": "123456",
    "new_password": "NewSecurePass123!",
    "confirm_password": "NewSecurePass123!"
}

Response (200 OK):
{
    "message": "Password reset successful. Please login with your new password."
}

Note: All existing tokens are deleted (user must re-login)


==========================================
LOGOUT
==========================================
POST /api/users/auth/logout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

Response (200 OK):
{
    "message": "Logout successful"
}


==========================================
OTP FEATURES & SECURITY
==========================================

1. OTP Validity:
   - Valid for 10 minutes from generation
   - 6-digit numeric code

2. Rate Limiting:
   - Maximum 3 OTP requests per 30 minutes per user
   - Prevents spam and abuse

3. Maximum Attempts:
   - 5 attempts per OTP
   - After 5 failed attempts, must request new OTP

4. OTP Purposes:
   - registration: Email verification during signup
   - login: Passwordless login
   - password_reset: Reset forgotten password
   - email_change: Verify new email address

5. Security Features:
   - OTPs are single-use
   - Expired OTPs are automatically invalid
   - Failed attempts are tracked
   - Email verification required for full access

6. Email Templates:
   - Professional HTML emails
   - Clear instructions
   - Branded content
   - Mobile-responsive


==========================================
ERROR RESPONSES
==========================================

400 Bad Request:
{
    "error": "Invalid OTP. 3 attempts remaining"
}

{
    "error": "OTP has expired or maximum attempts reached"
}

{
    "error": "Passwords do not match"
}

403 Forbidden:
{
    "error": "Email not verified. Please verify your email first.",
    "email": "john@example.com",
    "user_id": 1,
    "action": "Request OTP at /api/users/auth/resend-otp/"
}

404 Not Found:
{
    "error": "User not found"
}

{
    "error": "No OTP found. Please request a new one."
}

429 Too Many Requests:
{
    "error": "Too many OTP requests. Please try again after 30 minutes."
}

500 Internal Server Error:
{
    "error": "Failed to send OTP email. Please try again."
}


==========================================
FRONTEND INTEGRATION EXAMPLES
==========================================

JavaScript Example - Complete Registration Flow:
------------------------------------------------

// Step 1: Register
async function register(userData) {
    const response = await fetch('/api/users/auth/register/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: userData.username,
            email: userData.email,
            password: userData.password,
            confirm_password: userData.confirmPassword,
            first_name: userData.firstName,
            last_name: userData.lastName,
            user_type: 'patient',
            phone: userData.phone
        })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Store email for OTP verification
        sessionStorage.setItem('pendingEmail', data.email);
        // Redirect to OTP verification page
        window.location.href = '/verify-otp';
    }
    return data;
}

// Step 2: Verify OTP
async function verifyOTP(email, otp) {
    const response = await fetch('/api/users/auth/verify-otp/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: email,
            otp: otp,
            purpose: 'registration'
        })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Store token
        localStorage.setItem('token', data.token);
        localStorage.setItem('userId', data.user_id);
        // Redirect to dashboard
        window.location.href = '/dashboard';
    }
    return data;
}

// Step 3: Resend OTP
async function resendOTP(email) {
    const response = await fetch('/api/users/auth/resend-otp/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: email,
            purpose: 'registration'
        })
    });
    return await response.json();
}


React Example - OTP Verification Component:
-------------------------------------------

import React, { useState } from 'react';

function OTPVerification({ email, purpose = 'registration' }) {
    const [otp, setOtp] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    const handleVerify = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch('/api/users/auth/verify-otp/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email, otp, purpose })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('token', data.token);
                window.location.href = '/dashboard';
            } else {
                setError(data.error || 'Verification failed');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };
    
    const handleResend = async () => {
        try {
            const response = await fetch('/api/users/auth/resend-otp/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email, purpose })
            });
            
            const data = await response.json();
            alert(data.message);
        } catch (err) {
            alert('Failed to resend OTP');
        }
    };
    
    return (
        <div>
            <h2>Verify Your Email</h2>
            <p>We've sent a 6-digit code to {email}</p>
            
            <form onSubmit={handleVerify}>
                <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="Enter OTP"
                    maxLength="6"
                    required
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Verifying...' : 'Verify'}
                </button>
            </form>
            
            {error && <p style={{color: 'red'}}>{error}</p>}
            
            <button onClick={handleResend}>Resend OTP</button>
        </div>
    );
}

export default OTPVerification;


==========================================
TESTING CHECKLIST
==========================================

1. Registration Flow:
   ✓ User can register with valid data
   ✓ OTP email is sent
   ✓ OTP can be verified successfully
   ✓ Invalid OTP is rejected
   ✓ Expired OTP is rejected
   ✓ Rate limiting works
   ✓ Welcome email is sent after verification

2. Login Flow:
   ✓ Password login works for verified users
   ✓ Password login blocked for unverified users
   ✓ OTP login request works
   ✓ OTP login verification works

3. Password Reset:
   ✓ Reset OTP is sent
   ✓ Password can be reset with valid OTP
   ✓ All tokens are deleted after reset

4. Edge Cases:
   ✓ Duplicate email registration is prevented
   ✓ Duplicate username registration is prevented
   ✓ OTP resend rate limiting works
   ✓ Maximum attempts enforcement works
   ✓ Email sending failures are handled gracefully
"""