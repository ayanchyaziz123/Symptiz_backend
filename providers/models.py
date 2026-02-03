# ==================== doctors/models.py ====================
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User

class Specialty(models.Model):
    """Medical specialties"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=10, default='👨‍⚕️')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Specialties'
        ordering = ['name']


class Clinic(models.Model):
    """Healthcare facilities"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    # Location coordinates for mapping
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Clinic type
    CLINIC_TYPE_CHOICES = (
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('urgent_care', 'Urgent Care'),
        ('free_clinic', 'Free Clinic'),
        ('community_center', 'Community Health Center'),
    )
    clinic_type = models.CharField(max_length=20, choices=CLINIC_TYPE_CHOICES, default='clinic')
    
    # Affordability
    accepts_medicaid = models.BooleanField(default=False)
    accepts_medicare = models.BooleanField(default=False)
    sliding_scale = models.BooleanField(default=False)
    free_services = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Provider(models.Model):
    """Healthcare provider profiles"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')

    # Professional Info
    specialties = models.ManyToManyField(Specialty, related_name='providers')
    license_number = models.CharField(max_length=50, unique=True)
    license_document = models.FileField(upload_to='provider_licenses/', blank=True, null=True,
                                       help_text="Upload medical license document (PDF, JPG, PNG)")
    years_experience = models.IntegerField(validators=[MinValueValidator(0)])
    bio = models.TextField(blank=True)
    education = models.TextField(blank=True, help_text="Medical education background")
    certifications = models.TextField(blank=True, help_text="Board certifications and additional qualifications")

    # Languages
    languages = models.CharField(max_length=200, help_text="Comma-separated list")

    # Clinic affiliation
    clinics = models.ManyToManyField(Clinic, related_name='providers', through='ProviderClinicAffiliation')

    # Ratings & Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    total_reviews = models.IntegerField(default=0)

    # Availability
    accepting_new_patients = models.BooleanField(default=True)
    video_visit_available = models.BooleanField(default=False)

    # Verification & Admin
    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES,
                                          default='pending')
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='verified_providers',
                                   help_text="Admin who verified this provider")
    rejection_reason = models.TextField(blank=True, help_text="Reason if rejected")

    # Payment & Stripe
    stripe_account_id = models.CharField(max_length=100, blank=True, null=True,
                                         help_text="Stripe Connect account ID for payments")
    stripe_onboarding_complete = models.BooleanField(default=False)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00,
                                          validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
                                          help_text="Platform commission percentage (default 15%)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}"
    
    class Meta:
        ordering = ['-average_rating', '-created_at']


class ProviderClinicAffiliation(models.Model):
    """Links providers to clinics with additional info"""
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return f"{self.provider} at {self.clinic}"
    
    class Meta:
        unique_together = ('provider', 'clinic')


class ProviderAvailability(models.Model):
    """Provider's weekly schedule"""
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='availability')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.provider} - {self.get_day_of_week_display()}"
    
    class Meta:
        ordering = ['day_of_week', 'start_time']


class Review(models.Model):
    """Patient reviews for providers"""
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    visit_date = models.DateField(blank=True, null=True)
    would_recommend = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Review for {self.provider} by {self.patient}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('provider', 'patient')