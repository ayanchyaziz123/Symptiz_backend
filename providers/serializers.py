# ==================== providers/serializers.py ====================
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    Specialty, Clinic, Provider, ProviderClinicAffiliation,
    ProviderAvailability, Review
)
from users.models import User
from users.serializers import UserProfileSerializer


class SpecialtySerializer(serializers.ModelSerializer):
    """Serializer for Specialty model"""
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'icon', 'description']
        read_only_fields = ['id']


class ClinicSerializer(serializers.ModelSerializer):
    """Serializer for Clinic model"""
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'address', 'city', 'state', 'zip_code',
            'phone', 'email', 'latitude', 'longitude', 'clinic_type',
            'accepts_medicaid', 'accepts_medicare', 'sliding_scale',
            'free_services', 'created_at', 'distance'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_distance(self, obj):
        """Calculate distance if user coordinates provided in context"""
        # This would require additional logic with user location
        return None


class ClinicListSerializer(serializers.ModelSerializer):
    """Simplified serializer for clinic lists"""
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'address', 'city', 'state', 'phone',
            'clinic_type', 'accepts_medicaid', 'accepts_medicare'
        ]
        read_only_fields = ['id']


class ProviderClinicAffiliationSerializer(serializers.ModelSerializer):
    """Serializer for Provider-Clinic relationship"""
    clinic = ClinicListSerializer(read_only=True)
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        source='clinic',
        write_only=True
    )
    
    class Meta:
        model = ProviderClinicAffiliation
        fields = ['id', 'clinic', 'clinic_id', 'is_primary', 'consultation_fee']
        read_only_fields = ['id']


class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for Provider availability schedule"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    clinic = serializers.PrimaryKeyRelatedField(queryset=Clinic.objects.all(), required=False, allow_null=True)

    class Meta:
        model = ProviderAvailability
        fields = [
            'id', 'clinic', 'clinic_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_active'
        ]
        read_only_fields = ['id']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Provider reviews"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    provider_name = serializers.CharField(source='provider.__str__', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'provider', 'provider_name', 'patient', 'patient_id', 'patient_name',
            'rating', 'comment', 'visit_date', 'would_recommend',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Ensure rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews"""
    class Meta:
        model = Review
        fields = ['provider', 'rating', 'comment', 'visit_date', 'would_recommend']
    
    def create(self, validated_data):
        """Add patient from request context"""
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class ProviderSerializer(serializers.ModelSerializer):
    """Main serializer for Provider model"""
    user = UserProfileSerializer(read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)
    specialty_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialty.objects.all(),
        source='specialties',
        write_only=True
    )
    clinics_info = ProviderClinicAffiliationSerializer(
        source='providerclinicaffiliation_set',
        many=True,
        read_only=True
    )
    recent_reviews = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id', 'user', 'full_name', 'specialties', 'specialty_ids',
            'license_number', 'years_experience', 'bio', 'languages',
            'clinics_info', 'average_rating', 'total_reviews',
            'accepting_new_patients', 'video_visit_available',
            'is_verified', 'verified_at', 'recent_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'average_rating', 'total_reviews', 'is_verified',
            'verified_at', 'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        return obj.__str__()
    
    def get_recent_reviews(self, obj):
        """Get 3 most recent reviews"""
        reviews = obj.reviews.all()[:3]
        return ReviewSerializer(reviews, many=True).data


class ProviderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for provider lists"""
    full_name = serializers.SerializerMethodField()
    specialties = serializers.StringRelatedField(many=True)
    primary_clinic = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id', 'full_name', 'specialties', 'years_experience',
            'average_rating', 'total_reviews', 'accepting_new_patients',
            'video_visit_available', 'primary_clinic'
        ]
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.__str__()
    
    def get_primary_clinic(self, obj):
        """Get provider's primary clinic"""
        affiliation = obj.providerclinicaffiliation_set.filter(is_primary=True).first()
        if affiliation:
            return ClinicListSerializer(affiliation.clinic).data
        return None


class ProviderDetailSerializer(ProviderSerializer):
    """Detailed serializer for single provider view"""
    availability = ProviderAvailabilitySerializer(many=True, read_only=True)
    all_reviews = serializers.SerializerMethodField()
    
    class Meta(ProviderSerializer.Meta):
        fields = ProviderSerializer.Meta.fields + ['availability', 'all_reviews']
    
    def get_all_reviews(self, obj):
        """Get all reviews with pagination info"""
        reviews = obj.reviews.all()[:10]  # Limit to 10 for detail view
        return ReviewSerializer(reviews, many=True).data


class ProviderRegistrationSerializer(serializers.Serializer):
    """Serializer for provider registration with license upload"""
    # User fields
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Provider-specific fields
    license_number = serializers.CharField(max_length=50)
    license_document = serializers.FileField(required=False, allow_null=True)
    years_experience = serializers.IntegerField(min_value=0)
    bio = serializers.CharField(required=False, allow_blank=True)
    education = serializers.CharField(required=False, allow_blank=True)
    certifications = serializers.CharField(required=False, allow_blank=True)
    languages = serializers.CharField(default='English')
    specialty_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )

    def validate(self, attrs):
        """Validate passwords match and email/username unique"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})

        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already registered"})

        if Provider.objects.filter(license_number=attrs['license_number']).exists():
            raise serializers.ValidationError({"license_number": "License number already registered"})

        return attrs

    def create(self, validated_data):
        """Create user and provider profile"""
        # Extract specialty IDs
        specialty_ids = validated_data.pop('specialty_ids')
        validated_data.pop('confirm_password')

        # Extract provider-specific fields
        license_number = validated_data.pop('license_number')
        license_document = validated_data.pop('license_document', None)
        years_experience = validated_data.pop('years_experience')
        bio = validated_data.pop('bio', '')
        education = validated_data.pop('education', '')
        certifications = validated_data.pop('certifications', '')
        languages = validated_data.pop('languages', 'English')

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
            user_type='provider'
        )

        # Create provider profile
        provider = Provider.objects.create(
            user=user,
            license_number=license_number,
            license_document=license_document,
            years_experience=years_experience,
            bio=bio,
            education=education,
            certifications=certifications,
            languages=languages,
            verification_status='pending',
            is_verified=False
        )

        # Add specialties
        for specialty_id in specialty_ids:
            try:
                specialty = Specialty.objects.get(id=specialty_id)
                provider.specialties.add(specialty)
            except Specialty.DoesNotExist:
                pass

        return {'user': user, 'provider': provider}