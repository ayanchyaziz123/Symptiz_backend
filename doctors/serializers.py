# ==================== doctors/serializers.py ====================
from rest_framework import serializers
from .models import (
    Specialty, Clinic, Doctor, DoctorClinicAffiliation,
    DoctorAvailability, Review
)
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


class DoctorClinicAffiliationSerializer(serializers.ModelSerializer):
    """Serializer for Doctor-Clinic relationship"""
    clinic = ClinicListSerializer(read_only=True)
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        source='clinic',
        write_only=True
    )
    
    class Meta:
        model = DoctorClinicAffiliation
        fields = ['id', 'clinic', 'clinic_id', 'is_primary', 'consultation_fee']
        read_only_fields = ['id']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for Doctor availability schedule"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    
    class Meta:
        model = DoctorAvailability
        fields = [
            'id', 'clinic', 'clinic_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_active'
        ]
        read_only_fields = ['id']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Doctor reviews"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.__str__', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_id', 'patient_name',
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
        fields = ['doctor', 'rating', 'comment', 'visit_date', 'would_recommend']
    
    def create(self, validated_data):
        """Add patient from request context"""
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class DoctorSerializer(serializers.ModelSerializer):
    """Main serializer for Doctor model"""
    user = UserProfileSerializer(read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)
    specialty_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialty.objects.all(),
        source='specialties',
        write_only=True
    )
    clinics_info = DoctorClinicAffiliationSerializer(
        source='doctorclinicaffiliation_set',
        many=True,
        read_only=True
    )
    recent_reviews = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
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


class DoctorListSerializer(serializers.ModelSerializer):
    """Simplified serializer for doctor lists"""
    full_name = serializers.SerializerMethodField()
    specialties = serializers.StringRelatedField(many=True)
    primary_clinic = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'specialties', 'years_experience',
            'average_rating', 'total_reviews', 'accepting_new_patients',
            'video_visit_available', 'primary_clinic'
        ]
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.__str__()
    
    def get_primary_clinic(self, obj):
        """Get doctor's primary clinic"""
        affiliation = obj.doctorclinicaffiliation_set.filter(is_primary=True).first()
        if affiliation:
            return ClinicListSerializer(affiliation.clinic).data
        return None


class DoctorDetailSerializer(DoctorSerializer):
    """Detailed serializer for single doctor view"""
    availability = DoctorAvailabilitySerializer(many=True, read_only=True)
    all_reviews = serializers.SerializerMethodField()
    
    class Meta(DoctorSerializer.Meta):
        fields = DoctorSerializer.Meta.fields + ['availability', 'all_reviews']
    
    def get_all_reviews(self, obj):
        """Get all reviews with pagination info"""
        reviews = obj.reviews.all()[:10]  # Limit to 10 for detail view
        return ReviewSerializer(reviews, many=True).data