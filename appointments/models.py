# ==================== appointments/models.py ====================
from django.db import models
from django.utils import timezone
from doctors.models import Doctor, Clinic
from users.models import User

class Appointment(models.Model):
    """Patient appointments with doctors"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    )
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='appointments')
    
    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    
    # Patient info
    reason = models.TextField(blank=True)
    insurance_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Type
    APPOINTMENT_TYPE_CHOICES = (
        ('in_person', 'In-Person'),
        ('video', 'Video Call'),
        ('phone', 'Phone Call'),
    )
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='in_person')
    
    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    doctor_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date}"
    
    @property
    def is_upcoming(self):
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime > now
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']


class AppointmentReminder(models.Model):
    """Track appointment reminders"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    
    REMINDER_TYPE_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
    )
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPE_CHOICES)
    
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.reminder_type} reminder for {self.appointment}"
    
    class Meta:
        ordering = ['scheduled_for']