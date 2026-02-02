# ==================== appointments/views.py ====================
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .models import Appointment, AppointmentReminder
from .serializers import (
    AppointmentSerializer, AppointmentCreateSerializer,
    AppointmentUpdateSerializer, AppointmentListSerializer,
    PatientAppointmentSerializer, DoctorAppointmentSerializer,
    AppointmentReminderSerializer
)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment CRUD operations
    """
    queryset = Appointment.objects.select_related(
        'patient', 'doctor', 'clinic'
    ).prefetch_related('doctor__user', 'doctor__specialties')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_type', 'doctor', 'clinic']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at']
    ordering = ['-appointment_date', '-appointment_time']
    
    def get_queryset(self):
        """Filter appointments based on user type"""
        user = self.request.user
        
        if user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
        elif user.user_type == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        elif user.is_staff:
            return Appointment.objects.all()
        
        return Appointment.objects.none()
    
    def get_serializer_class(self):
        """Use different serializers based on action and user type"""
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        elif self.action == 'list':
            user = self.request.user
            if user.user_type == 'patient':
                return PatientAppointmentSerializer
            elif user.user_type == 'doctor':
                return DoctorAppointmentSerializer
            return AppointmentListSerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        """Set patient to current user"""
        serializer.save(patient=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        queryset = self.get_queryset().filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('appointment_date', 'appointment_time')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get past appointments"""
        queryset = self.get_queryset().filter(
            Q(appointment_date__lt=timezone.now().date()) |
            Q(status__in=['completed', 'cancelled', 'no_show'])
        ).order_by('-appointment_date', '-appointment_time')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            appointment_date=today
        ).order_by('appointment_time')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        
        if appointment.status != 'pending':
            return Response(
                {'error': 'Only pending appointments can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'confirmed'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        if appointment.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'This appointment cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancellation_reason = request.data.get('reason', '')
        appointment.status = 'cancelled'
        appointment.doctor_notes = f"Cancelled: {cancellation_reason}"
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark appointment as completed (doctors only)"""
        user = request.user
        appointment = self.get_object()
        
        if user.user_type != 'doctor' or appointment.doctor.user != user:
            return Response(
                {'error': 'Only the assigned doctor can complete appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed appointments can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'completed'
        doctor_notes = request.data.get('doctor_notes', '')
        if doctor_notes:
            appointment.doctor_notes = doctor_notes
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an appointment"""
        appointment = self.get_object()
        
        if appointment.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'This appointment cannot be rescheduled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_date = request.data.get('appointment_date')
        new_time = request.data.get('appointment_time')
        
        if not new_date or not new_time:
            return Response(
                {'error': 'New date and time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.status = 'pending'  # Reset to pending for confirmation
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a doctor"""
        doctor_id = request.query_params.get('doctor_id')
        date = request.query_params.get('date')
        
        if not doctor_id or not date:
            return Response(
                {'error': 'doctor_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get existing appointments for this doctor on this date
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=date_obj,
            status__in=['pending', 'confirmed']
        ).values_list('appointment_time', flat=True)
        
        # Generate available slots (example: 9 AM to 5 PM, 30-min slots)
        # This is simplified - you'd want to check doctor's actual availability
        from datetime import time
        available_slots = []
        start_time = time(9, 0)
        end_time = time(17, 0)
        current_time = start_time
        
        while current_time < end_time:
            if current_time not in booked_appointments:
                available_slots.append(current_time.strftime('%H:%M'))
            
            # Add 30 minutes
            dt = datetime.combine(date_obj, current_time)
            dt += timedelta(minutes=30)
            current_time = dt.time()
        
        return Response({'available_slots': available_slots})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get appointment statistics (for doctors/admins)"""
        user = request.user
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'confirmed': queryset.filter(status='confirmed').count(),
            'completed': queryset.filter(status='completed').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'no_show': queryset.filter(status='no_show').count(),
            'upcoming': queryset.filter(
                appointment_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            ).count()
        }
        
        return Response(stats)


class AppointmentReminderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing appointment reminders (read-only)
    """
    queryset = AppointmentReminder.objects.select_related('appointment')
    serializer_class = AppointmentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter reminders based on user"""
        user = self.request.user
        
        if user.user_type == 'patient':
            return AppointmentReminder.objects.filter(
                appointment__patient=user
            )
        elif user.user_type == 'doctor':
            return AppointmentReminder.objects.filter(
                appointment__doctor__user=user
            )
        
        return AppointmentReminder.objects.all()


# Import Q for complex queries
from django.db.models import Q