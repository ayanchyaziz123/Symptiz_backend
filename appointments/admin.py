# ==================== appointments/admin.py ====================
from django.contrib import admin
from .models import Appointment, AppointmentReminder

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'clinic', 'appointment_date', 'appointment_time', 'status', 'appointment_type')
    list_filter = ('status', 'appointment_type', 'appointment_date', 'clinic')
    search_fields = ('patient__username', 'doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'appointment_date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'doctor', 'clinic')
        }),
        ('Schedule', {
            'fields': ('appointment_date', 'appointment_time', 'duration_minutes', 'appointment_type')
        }),
        ('Details', {
            'fields': ('reason', 'insurance_type', 'status')
        }),
        ('Reminders', {
            'fields': ('reminder_sent', 'reminder_sent_at')
        }),
        ('Notes', {
            'fields': ('doctor_notes',)
        }),
    )


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'reminder_type', 'scheduled_for', 'is_sent', 'sent_at')
    list_filter = ('reminder_type', 'is_sent', 'scheduled_for')
    readonly_fields = ('created_at',)