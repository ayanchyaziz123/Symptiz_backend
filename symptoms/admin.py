from django.contrib import admin
from .models import SymptomCategory, SymptomCheck, HealthTip


@admin.register(SymptomCategory)
class SymptomCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(SymptomCheck)
class SymptomCheckAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'patient',
        'urgency_level',
        'recommended_provider_type',
        'confidence_score',
        'appointment_booked',
        'created_at'
    ]
    list_filter = [
        'urgency_level',
        'appointment_booked',
        'follow_up_needed',
        'created_at'
    ]
    search_fields = [
        'symptoms_description',
        'patient__username',
        'patient__email',
        'recommendation'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'session_id',
        'ip_address',
        'confidence_score',
        'ai_metadata'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'session_id', 'ip_address')
        }),
        ('Symptoms', {
            'fields': ('symptoms_description',)
        }),
        ('AI Analysis', {
            'fields': (
                'urgency_level',
                'recommended_provider_type',
                'recommendation',
                'confidence_score',
                'possible_conditions',
                'ai_metadata'
            )
        }),
        ('Follow-up', {
            'fields': ('follow_up_needed', 'appointment_booked')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'category', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']