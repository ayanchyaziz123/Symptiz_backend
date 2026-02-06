# ==================== users/models.py (ADD THIS TO YOUR EXISTING USER MODEL) ====================
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
import string


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('provider', 'Provider'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Patient-specific fields
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_id = models.CharField(max_length=50, blank=True, null=True)
    insurance_document = models.FileField(upload_to='insurance_documents/', blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Preferences
    email_reminders = models.BooleanField(default=True)
    sms_reminders = models.BooleanField(default=True)
    
    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"
    
    class Meta:
        ordering = ['-created_at']


class EmailOTP(models.Model):
    """Email OTP for verification"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    
    # OTP purpose
    PURPOSE_CHOICES = (
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='registration')
    
    # Status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Expiry
    expires_at = models.DateTimeField()
    
    # Attempts
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"OTP for {self.email} - {self.purpose}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
    
    @classmethod
    def generate_otp(cls, user, email, purpose='registration', validity_minutes=10):
        """Generate a new OTP"""
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Set expiry time
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        
        # Create OTP record
        otp_obj = cls.objects.create(
            user=user,
            email=email,
            otp=otp,
            purpose=purpose,
            expires_at=expires_at
        )
        
        return otp_obj
    
    def is_valid(self):
        """Check if OTP is still valid"""
        if self.is_verified:
            return False
        if self.attempts >= self.max_attempts:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def verify(self, otp_input):
        """Verify the OTP"""
        self.attempts += 1
        self.save()
        
        if not self.is_valid():
            return False, "OTP has expired or maximum attempts reached"
        
        if self.otp != otp_input:
            remaining = self.max_attempts - self.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining"
        
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()
        
        # Update user email verification
        if self.purpose in ['registration', 'email_change']:
            self.user.is_email_verified = True
            self.user.email_verified_at = timezone.now()
            self.user.save()
        
        return True, "OTP verified successfully"
    
    @classmethod
    def cleanup_expired(cls):
        """Delete expired OTPs (run as periodic task)"""
        expired = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        return count