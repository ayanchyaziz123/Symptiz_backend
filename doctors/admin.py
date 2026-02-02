# ==================== doctors/admin.py ====================
from django.contrib import admin
from .models import Specialty, Clinic, Doctor, DoctorClinicAffiliation, DoctorAvailability, Review

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'clinic_type', 'accepts_medicaid', 'sliding_scale')
    list_filter = ('clinic_type', 'accepts_medicaid', 'accepts_medicare', 'sliding_scale', 'free_services')
    search_fields = ('name', 'city', 'address')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'clinic_type', 'phone', 'email')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Affordability Options', {
            'fields': ('accepts_medicaid', 'accepts_medicare', 'sliding_scale', 'free_services')
        }),
    )


class DoctorClinicAffiliationInline(admin.TabularInline):
    model = DoctorClinicAffiliation
    extra = 1


class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 3


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_specialties', 'years_experience', 'average_rating', 'accepting_new_patients', 'is_verified')
    list_filter = ('accepting_new_patients', 'video_visit_available', 'is_verified', 'specialties')
    search_fields = ('user__first_name', 'user__last_name', 'license_number')
    filter_horizontal = ('specialties',)
    inlines = [DoctorClinicAffiliationInline, DoctorAvailabilityInline]
    
    def get_specialties(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()])
    get_specialties.short_description = 'Specialties'
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('specialties', 'license_number', 'years_experience', 'bio', 'languages')
        }),
        ('Ratings', {
            'fields': ('average_rating', 'total_reviews')
        }),
        ('Availability', {
            'fields': ('accepting_new_patients', 'video_visit_available')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'rating', 'would_recommend', 'created_at')
    list_filter = ('rating', 'would_recommend', 'created_at')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name', 'patient__username')
    readonly_fields = ('created_at', 'updated_at')
