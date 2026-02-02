# ==================== appointments/serializers.py ====================
from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentReminder
from doctors.serializers import DoctorListSerializer, ClinicListSerializer
from users.serializers import UserProfileSerializer


class AppointmentReminderSerializer(serializers.ModelSerializer):
    """Serializer for Appointment reminders"""
    class Meta:
        model = AppointmentReminder
        fields = [
            'id', 'appointment', 'reminder_type', 'scheduled_for',
            'sent_at', 'is_sent', 'created_at'
        ]
        read_only_fields = ['id', 'sent_at', 'is_sent', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """Main serializer for Appointment model"""
    patient_info = UserProfileSerializer(source='patient', read_only=True)
    doctor_info = DoctorListSerializer(source='doctor', read_only=True)
    clinic_info = ClinicListSerializer(source='clinic', read_only=True)
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appointment_type_display = serializers.CharField(
        source='get_appointment_type_display',
        read_only=True
    )
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_info', 'doctor', 'doctor_info',
            'clinic', 'clinic_info', 'appointment_date', 'appointment_time',
            'duration_minutes', 'reason', 'insurance_type', 'status',
            'status_display', 'appointment_type', 'appointment_type_display',
            'reminder_sent', 'reminder_sent_at', 'doctor_notes',
            'is_upcoming', 'reminders', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reminder_sent', 'reminder_sent_at', 'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Validate appointment date and time"""
        appointment_date = attrs.get('appointment_date')
        appointment_time = attrs.get('appointment_time')
        
        if appointment_date and appointment_time:
            appointment_datetime = timezone.datetime.combine(
                appointment_date,
                appointment_time
            )
            appointment_datetime = timezone.make_aware(appointment_datetime)
            
            if appointment_datetime <= timezone.now():
                raise serializers.ValidationError(
                    "Appointment must be scheduled for a future date and time"
                )
        
        return attrs
    
    def validate_doctor_availability(self, attrs):
        """Check if doctor is available at the requested time"""
        # This would require checking DoctorAvailability
        # Implementation depends on your business logic
        return attrs


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""
    class Meta:
        model = Appointment
        fields = [
            'doctor', 'clinic', 'appointment_date', 'appointment_time',
            'duration_minutes', 'reason', 'insurance_type', 'appointment_type'
        ]
    
    def create(self, validated_data):
        """Add patient from request context"""
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""
    class Meta:
        model = Appointment
        fields = [
            'appointment_date', 'appointment_time', 'reason',
            'insurance_type', 'appointment_type', 'status'
        ]
    
    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance
        if instance:
            # Define valid status transitions
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'cancelled': [],
                'completed': [],
                'no_show': []
            }
            
            if value not in valid_transitions.get(instance.status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {instance.status} to {value}"
                )
        
        return value


class AppointmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for appointment lists"""
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.__str__', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_name', 'doctor_name', 'clinic_name',
            'appointment_date', 'appointment_time', 'status',
            'status_display', 'appointment_type', 'is_upcoming'
        ]
        read_only_fields = ['id']


class PatientAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for patient's view of their appointments"""
    doctor_info = DoctorListSerializer(source='doctor', read_only=True)
    clinic_info = ClinicListSerializer(source='clinic', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_info', 'clinic_info', 'appointment_date',
            'appointment_time', 'duration_minutes', 'reason',
            'status', 'status_display', 'appointment_type',
            'is_upcoming', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for doctor's view of their appointments"""
    patient_info = UserProfileSerializer(source='patient', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_info', 'clinic_name', 'appointment_date',
            'appointment_time', 'duration_minutes', 'reason',
            'insurance_type', 'status', 'status_display',
            'appointment_type', 'doctor_notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']