# ==================== users/views.py (WITH OTP VERIFICATION) ====================
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db import models

from .models import User, EmailOTP
from .serializers import (
    UserSerializer, UserProfileSerializer, PatientSerializer,
    UserRegistrationSerializer, EmailOTPSerializer,
    SendOTPSerializer, VerifyOTPSerializer, ResendOTPSerializer,
    LoginWithOTPSerializer, PasswordResetSerializer
)
from .utils import send_otp_email, send_welcome_email


class RegisterView(APIView):
    """
    Step 1: Register user and send OTP
    
    POST /api/users/auth/register/
    Body: {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "user_type": "patient",
        "phone": "555-1234"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        # 🔍 Check if user already exists
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            # ❌ If already verified → block
            if existing_user.is_email_verified:
                return Response({
                'error': 'User already exists. Please login.'
            }, status=status.HTTP_400_BAD_REQUEST)

            # 🔄 If not verified → resend OTP
            otp_obj = EmailOTP.generate_otp(
            user=existing_user,
            email=email,
            purpose='registration',
            validity_minutes=10
                )

            send_otp_email(
              email=email,
              otp=otp_obj.otp,
              purpose='registration',
              user_name=existing_user.first_name or existing_user.username
               )

            return Response({
              'message': 'Email already registered but not verified. OTP resent.',
              'user_id': existing_user.id,
              'email': email,
              'otp_expires_in_minutes': 10,
              'next_step': 'Verify OTP at /api/users/auth/verify-otp/'
             }, status=status.HTTP_200_OK)

        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Create user
            user = serializer.save()
            
            # Generate OTP
            otp_obj = EmailOTP.generate_otp(
                user=user,
                email=user.email,
                purpose='registration',
                validity_minutes=10
            )
            
            # Send OTP email
            email_sent = send_otp_email(
                email=user.email,
                otp=otp_obj.otp,
                purpose='registration',
                user_name=user.first_name or user.username
            )
            
            if not email_sent:
                return Response({
                    'error': 'Failed to send OTP email. Please try again.',
                    'user_id': user.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'Registration successful. Please check your email for OTP.',
                'user_id': user.id,
                'email': user.email,
                'otp_expires_in_minutes': 10,
                'next_step': 'Verify OTP at /api/users/auth/verify-otp/'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    Step 2: Verify OTP and complete registration/login
    
    POST /api/users/auth/verify-otp/
    Body: {
        "email": "john@example.com",
        "otp": "123456",
        "purpose": "registration"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest unverified OTP for this purpose
        otp_obj = EmailOTP.objects.filter(
            user=user,
            email=email,
            purpose=purpose,
            is_verified=False
        ).order_by('-created_at').first()
        
        if not otp_obj:
            return Response({
                'error': 'No OTP found. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        is_valid, message = otp_obj.verify(otp_input)
        
        if not is_valid:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP verified successfully
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Send welcome email for registration
        if purpose == 'registration':
            send_welcome_email(user)
        
        return Response({
            'message': 'OTP verified successfully',
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'is_email_verified': user.is_email_verified
        }, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """
    Resend OTP
    
    POST /api/users/auth/resend-otp/
    Body: {
        "email": "john@example.com",
        "purpose": "registration"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user already verified for registration
        if purpose == 'registration' and user.is_email_verified:
            return Response({
                'error': 'Email already verified. Please login.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rate limiting (max 3 OTPs in 30 minutes)
        recent_otps = EmailOTP.objects.filter(
            user=user,
            email=email,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(minutes=30)
        ).count()
        
        if recent_otps >= 3:
            return Response({
                'error': 'Too many OTP requests. Please try again after 30 minutes.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate new OTP
        otp_obj = EmailOTP.generate_otp(
            user=user,
            email=email,
            purpose=purpose,
            validity_minutes=10
        )
        
        # Send OTP email
        email_sent = send_otp_email(
            email=email,
            otp=otp_obj.otp,
            purpose=purpose,
            user_name=user.first_name or user.username
        )
        
        if not email_sent:
            return Response({
                'error': 'Failed to send OTP email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'OTP sent successfully. Please check your email.',
            'email': email,
            'otp_expires_in_minutes': 10
        }, status=status.HTTP_200_OK)


class LoginWithOTPView(APIView):
    """
    Step 1: Request OTP for login
    
    POST /api/users/auth/login-with-otp/
    Body: {
        "email": "john@example.com"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginWithOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'No account found with this email'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate OTP for login
        otp_obj = EmailOTP.generate_otp(
            user=user,
            email=email,
            purpose='login',
            validity_minutes=10
        )
        
        # Send OTP email
        email_sent = send_otp_email(
            email=email,
            otp=otp_obj.otp,
            purpose='login',
            user_name=user.first_name or user.username
        )
        
        if not email_sent:
            return Response({
                'error': 'Failed to send OTP email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'OTP sent successfully. Please check your email.',
            'email': email,
            'otp_expires_in_minutes': 10,
            'next_step': 'Verify OTP at /api/users/auth/verify-otp/ with purpose=login'
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    Traditional login with username/password (without OTP)
    
    POST /api/users/auth/login/
    Body: {
        "username": "john_doe",  // or "email": "john@example.com"
        "password": "SecurePass123!"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not password:
            return Response({
                'error': 'Password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = None
        if username:
            user = authenticate(username=username, password=password)
        elif email:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if email is verified
        if not user.is_email_verified:
            return Response({
                'error': 'Email not verified. Please verify your email first.',
                'email': user.email,
                'user_id': user.id,
                'action': 'Request OTP at /api/users/auth/resend-otp/'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_email_verified': user.is_email_verified,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class RequestPasswordResetView(APIView):
    """
    Request password reset OTP
    
    POST /api/users/auth/request-password-reset/
    Body: {
        "email": "john@example.com"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security)
            return Response({
                'message': 'If an account exists with this email, you will receive a password reset OTP.'
            }, status=status.HTTP_200_OK)
        
        # Generate OTP
        otp_obj = EmailOTP.generate_otp(
            user=user,
            email=email,
            purpose='password_reset',
            validity_minutes=10
        )
        
        # Send OTP email
        send_otp_email(
            email=email,
            otp=otp_obj.otp,
            purpose='password_reset',
            user_name=user.first_name or user.username
        )
        
        return Response({
            'message': 'If an account exists with this email, you will receive a password reset OTP.',
            'next_step': 'Use OTP to reset password at /api/users/auth/reset-password/'
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    Reset password with OTP
    
    POST /api/users/auth/reset-password/
    Body: {
        "email": "john@example.com",
        "otp": "123456",
        "new_password": "NewSecurePass123!",
        "confirm_password": "NewSecurePass123!"
    }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest OTP for password reset
        otp_obj = EmailOTP.objects.filter(
            user=user,
            email=email,
            purpose='password_reset',
            is_verified=False
        ).order_by('-created_at').first()
        
        if not otp_obj:
            return Response({
                'error': 'No OTP found. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        is_valid, message = otp_obj.verify(otp_input)
        
        if not is_valid:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user.set_password(new_password)
        user.save()
        
        # Delete all user's tokens (force re-login)
        Token.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password reset successful. Please login with your new password.'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout user

    POST /api/users/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfilePictureUploadView(APIView):
    """
    Upload or update profile picture

    POST /api/users/profile/picture/
    Content-Type: multipart/form-data
    Body: profile_picture (file)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'profile_picture' not in request.FILES:
            return Response({
                'error': 'No profile picture file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        profile_picture = request.FILES['profile_picture']

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return Response({
                'error': 'File size too large. Maximum size is 5MB.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete old profile picture if exists
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)

        # Save new profile picture
        user.profile_picture = profile_picture
        user.save()

        return Response({
            'message': 'Profile picture updated successfully',
            'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        """Delete profile picture"""
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=True)
            return Response({
                'message': 'Profile picture deleted successfully'
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'No profile picture to delete'
        }, status=status.HTTP_400_BAD_REQUEST)


class InsuranceDocumentUploadView(APIView):
    """
    Upload or update insurance document

    POST /api/users/insurance/document/
    Content-Type: multipart/form-data
    Body: insurance_document (file)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current insurance document info"""
        user = request.user
        if user.insurance_document:
            return Response({
                'has_document': True,
                'document_url': request.build_absolute_uri(user.insurance_document.url),
                'document_name': user.insurance_document.name.split('/')[-1],
            }, status=status.HTTP_200_OK)
        return Response({
            'has_document': False,
            'document_url': None,
            'document_name': None,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if 'insurance_document' not in request.FILES:
            return Response({
                'error': 'No insurance document file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        insurance_document = request.FILES['insurance_document']

        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif']
        if insurance_document.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only PDF, JPEG, PNG, and GIF are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 10MB for documents)
        if insurance_document.size > 10 * 1024 * 1024:
            return Response({
                'error': 'File size too large. Maximum size is 10MB.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete old insurance document if exists
        user = request.user
        if user.insurance_document:
            user.insurance_document.delete(save=False)

        # Save new insurance document
        user.insurance_document = insurance_document
        user.save()

        return Response({
            'message': 'Insurance document uploaded successfully',
            'document_url': request.build_absolute_uri(user.insurance_document.url) if user.insurance_document else None,
            'document_name': user.insurance_document.name.split('/')[-1] if user.insurance_document else None,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        """Delete insurance document"""
        user = request.user
        if user.insurance_document:
            user.insurance_document.delete(save=True)
            return Response({
                'message': 'Insurance document deleted successfully'
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'No insurance document to delete'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    Get and update user profile

    GET /api/users/profile/
    PUT/PATCH /api/users/profile/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'phone': user.phone,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'address': user.address,
            'city': user.city,
            'state': user.state,
            'zip_code': user.zip_code,
            'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
            'insurance_provider': user.insurance_provider,
            'insurance_id': user.insurance_id,
            'insurance_document': request.build_absolute_uri(user.insurance_document.url) if user.insurance_document else None,
            'insurance_document_name': user.insurance_document.name.split('/')[-1] if user.insurance_document else None,
            'emergency_contact_name': user.emergency_contact_name,
            'emergency_contact_phone': user.emergency_contact_phone,
            'email_reminders': user.email_reminders,
            'sms_reminders': user.sms_reminders,
            'is_email_verified': user.is_email_verified,
            'email_verified_at': user.email_verified_at.isoformat() if user.email_verified_at else None,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update_profile(request)

    def patch(self, request):
        return self._update_profile(request)

    def _update_profile(self, request):
        user = request.user
        data = request.data

        # Fields that can be updated
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'address', 'city', 'state', 'zip_code',
            'insurance_provider', 'insurance_id',
            'emergency_contact_name', 'emergency_contact_phone',
            'email_reminders', 'sms_reminders'
        ]

        for field in allowed_fields:
            if field in data:
                value = data[field]
                # Handle date_of_birth conversion
                if field == 'date_of_birth' and value:
                    try:
                        from datetime import datetime
                        if isinstance(value, str):
                            value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return Response({
                            'error': 'Invalid date format. Use YYYY-MM-DD'
                        }, status=status.HTTP_400_BAD_REQUEST)
                # Handle boolean fields
                elif field in ['email_reminders', 'sms_reminders']:
                    if isinstance(value, str):
                        value = value.lower() in ['true', '1', 'yes']
                setattr(user, field, value)

        user.save()

        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'phone': user.phone,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'zip_code': user.zip_code,
                'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                'insurance_provider': user.insurance_provider,
                'insurance_id': user.insurance_id,
                'emergency_contact_name': user.emergency_contact_name,
                'emergency_contact_phone': user.emergency_contact_phone,
                'email_reminders': user.email_reminders,
                'sms_reminders': user.sms_reminders,
            }
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Change user password

    POST /api/users/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not current_password or not new_password:
            return Response({
                'error': 'Current password and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)