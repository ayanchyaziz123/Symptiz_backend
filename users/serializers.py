# ==================== users/serializers.py (UPDATE WITH OTP SERIALIZERS) ====================
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, EmailOTP


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'user_type', 'phone', 'date_of_birth',
            'address', 'city', 'state', 'zip_code', 'profile_picture',
            'insurance_provider', 'insurance_id', 'emergency_contact_name',
            'emergency_contact_phone', 'email_reminders', 'sms_reminders',
            'is_email_verified', 'email_verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_email_verified', 'email_verified_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if 'password' in attrs:
            if attrs.get('password') != attrs.get('confirm_password'):
                raise serializers.ValidationError({
                    'confirm_password': 'Passwords do not match.'
                })
        return attrs
    
    def create(self, validated_data):
        """Create new user with encrypted password"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Simplified serializer for user profile display"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'profile_picture', 'city', 'state',
            'is_email_verified'
        ]
        read_only_fields = ['id', 'username', 'user_type', 'is_email_verified']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class PatientSerializer(serializers.ModelSerializer):
    """Serializer specifically for patient users"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'date_of_birth', 'address', 'city', 'state', 'zip_code',
            'insurance_provider', 'insurance_id', 'emergency_contact_name',
            'emergency_contact_phone', 'email_reminders', 'sms_reminders',
            'profile_picture', 'is_email_verified'
        ]
        read_only_fields = ['id', 'username', 'is_email_verified']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'user_type', 'phone'
        ]
    
    def validate_email(self, value):
        """Check if email is already registered"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def validate_username(self, value):
        """Check if username is already taken"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Create user but don't activate until email verification
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = True  # Keep active but mark email as unverified
        user.is_email_verified = False
        user.save()
        
        return user


class EmailOTPSerializer(serializers.ModelSerializer):
    """Serializer for EmailOTP model"""
    class Meta:
        model = EmailOTP
        fields = [
            'id', 'email', 'purpose', 'is_verified', 
            'expires_at', 'attempts', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'expires_at', 'attempts', 'created_at']


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=['registration', 'login', 'password_reset', 'email_change'],
        default='registration'
    )
    
    def validate_email(self, value):
        """Validate email based on purpose"""
        purpose = self.initial_data.get('purpose', 'registration')
        
        if purpose == 'registration':
            # For registration, email should not exist
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already registered.")
        else:
            # For other purposes, email should exist
            if not User.objects.filter(email=value).exists():
                raise serializers.ValidationError("No account found with this email.")
        
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    purpose = serializers.ChoiceField(
        choices=['registration', 'login', 'password_reset', 'email_change'],
        default='registration'
    )


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=['registration', 'login', 'password_reset', 'email_change'],
        default='registration'
    )


class LoginWithOTPSerializer(serializers.Serializer):
    """Serializer for login with OTP"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if user exists"""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset with OTP"""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return attrs