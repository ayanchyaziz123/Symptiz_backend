from rest_framework import serializers
from .models import SymptomCategory, SymptomCheck, HealthTip


class SymptomCategorySerializer(serializers.ModelSerializer):
    """Serializer for SymptomCategory"""
    
    class Meta:
        model = SymptomCategory
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class SymptomCheckCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SymptomCheck"""
    
    class Meta:
        model = SymptomCheck
        fields = [
            'symptoms_description',
            'urgency_level',
            'recommendation',
            'recommended_provider_type',
            'confidence_score',
            'possible_conditions',
            'follow_up_needed'
        ]
    
    def create(self, validated_data):
        """Create symptom check with optional patient"""
        request = self.context.get('request')
        
        # Associate with user if authenticated
        if request and request.user.is_authenticated:
            validated_data['patient'] = request.user
        
        # Capture session info
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['session_id'] = request.session.session_key
        
        return super().create(validated_data)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SymptomCheckSerializer(serializers.ModelSerializer):
    """Full serializer for SymptomCheck with all details"""
    patient_name = serializers.SerializerMethodField()
    possible_conditions_list = serializers.SerializerMethodField()
    
    class Meta:
        model = SymptomCheck
        fields = [
            'id',
            'patient',
            'patient_name',
            'symptoms_description',
            'urgency_level',
            'recommendation',
            'recommended_provider_type',
            'confidence_score',
            'possible_conditions',
            'possible_conditions_list',
            'follow_up_needed',
            'appointment_booked',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'patient',
            'created_at',
            'patient_name',
            'possible_conditions_list'
        ]
    
    def get_patient_name(self, obj):
        """Get patient full name or 'Anonymous'"""
        if obj.patient:
            return obj.patient.get_full_name()
        return 'Anonymous'
    
    def get_possible_conditions_list(self, obj):
        """Parse possible conditions JSON to list"""
        import json
        try:
            return json.loads(obj.possible_conditions) if obj.possible_conditions else []
        except (json.JSONDecodeError, TypeError):
            return []


class SymptomCheckListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing symptom checks"""
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SymptomCheck
        fields = [
            'id',
            'patient_name',
            'urgency_level',
            'recommended_provider_type',
            'appointment_booked',
            'created_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient:
            return obj.patient.get_full_name()
        return 'Anonymous'


class HealthTipSerializer(serializers.ModelSerializer):
    """Full serializer for HealthTip"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = HealthTip
        fields = [
            'id',
            'title',
            'content',
            'category',
            'category_name',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name']


class HealthTipListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing health tips"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthTip
        fields = [
            'id',
            'title',
            'content_preview',
            'category_name',
            'created_at'
        ]
    
    def get_content_preview(self, obj):
        """Return first 150 characters of content"""
        return obj.content[:150] + '...' if len(obj.content) > 150 else obj.content