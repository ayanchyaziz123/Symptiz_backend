# ==================== appointments/admin.py ====================
from django.contrib import admin
from .models import Appointment, AppointmentReminder


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'provider', 'clinic', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_type', 'appointment_date', 'clinic')
    search_fields = ('patient__first_name', 'patient__last_name', 'provider__user__first_name', 'provider__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Patient & Provider', {
            'fields': ('patient', 'provider', 'clinic')
        }),
        ('Appointment Details', {
            'fields': ('appointment_date', 'appointment_time', 'duration_minutes', 'appointment_type')
        }),
        ('Patient Information', {
            'fields': ('reason', 'insurance_type')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Reminders', {
            'fields': ('reminder_sent', 'reminder_sent_at')
        }),
        ('Notes', {
            'fields': ('provider_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'reminder_type', 'scheduled_for', 'is_sent', 'sent_at')
    list_filter = ('reminder_type', 'is_sent', 'scheduled_for')
    search_fields = ('appointment__patient__first_name', 'appointment__patient__last_name')
    readonly_fields = ('created_at',)