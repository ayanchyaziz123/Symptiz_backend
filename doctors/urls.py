# ==================== doctors/urls.py ====================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SpecialtyViewSet, ClinicViewSet, DoctorViewSet,
    DoctorClinicAffiliationViewSet, DoctorAvailabilityViewSet,
    ReviewViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'specialties', SpecialtyViewSet, basename='specialty')
router.register(r'clinics', ClinicViewSet, basename='clinic')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'affiliations', DoctorClinicAffiliationViewSet, basename='affiliation')
router.register(r'availability', DoctorAvailabilityViewSet, basename='availability')
router.register(r'reviews', ReviewViewSet, basename='review')

app_name = 'doctors'

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]

"""
API Endpoints:

Specialties:
    GET    /api/doctors/specialties/           - List all specialties
    GET    /api/doctors/specialties/{id}/      - Get specialty details

Clinics:
    GET    /api/doctors/clinics/               - List all clinics
    POST   /api/doctors/clinics/               - Create new clinic
    GET    /api/doctors/clinics/{id}/          - Get clinic details
    PUT    /api/doctors/clinics/{id}/          - Update clinic
    PATCH  /api/doctors/clinics/{id}/          - Partial update clinic
    DELETE /api/doctors/clinics/{id}/          - Delete clinic
    GET    /api/doctors/clinics/nearby/        - Find nearby clinics (requires latitude & longitude params)
    GET    /api/doctors/clinics/affordable/    - Get affordable clinics

Doctors:
    GET    /api/doctors/doctors/               - List all doctors
    POST   /api/doctors/doctors/               - Create new doctor
    GET    /api/doctors/doctors/{id}/          - Get doctor details
    PUT    /api/doctors/doctors/{id}/          - Update doctor
    PATCH  /api/doctors/doctors/{id}/          - Partial update doctor
    DELETE /api/doctors/doctors/{id}/          - Delete doctor
    GET    /api/doctors/doctors/search/        - Advanced doctor search
    GET    /api/doctors/doctors/{id}/reviews/  - Get reviews for specific doctor
    GET    /api/doctors/doctors/{id}/availability/ - Get availability for specific doctor
    GET    /api/doctors/doctors/recommended/   - Get recommended doctors (requires auth)

Doctor-Clinic Affiliations:
    GET    /api/doctors/affiliations/          - List all affiliations
    POST   /api/doctors/affiliations/          - Create new affiliation
    GET    /api/doctors/affiliations/{id}/     - Get affiliation details
    PUT    /api/doctors/affiliations/{id}/     - Update affiliation
    PATCH  /api/doctors/affiliations/{id}/     - Partial update affiliation
    DELETE /api/doctors/affiliations/{id}/     - Delete affiliation
    GET    /api/doctors/affiliations/by_doctor/ - Get affiliations by doctor (requires doctor_id param)

Doctor Availability:
    GET    /api/doctors/availability/          - List all availability schedules
    POST   /api/doctors/availability/          - Create new availability
    GET    /api/doctors/availability/{id}/     - Get availability details
    PUT    /api/doctors/availability/{id}/     - Update availability
    PATCH  /api/doctors/availability/{id}/     - Partial update availability
    DELETE /api/doctors/availability/{id}/     - Delete availability
    GET    /api/doctors/availability/by_doctor/ - Get availability by doctor (requires doctor_id param)

Reviews:
    GET    /api/doctors/reviews/               - List all reviews
    POST   /api/doctors/reviews/               - Create new review (requires auth)
    GET    /api/doctors/reviews/{id}/          - Get review details
    PUT    /api/doctors/reviews/{id}/          - Update review
    PATCH  /api/doctors/reviews/{id}/          - Partial update review
    DELETE /api/doctors/reviews/{id}/          - Delete review
    GET    /api/doctors/reviews/by_doctor/     - Get reviews by doctor (requires doctor_id param)
    GET    /api/doctors/reviews/my_reviews/    - Get current user's reviews (requires auth)

Search & Filter Examples:
    - /api/doctors/doctors/?search=john          - Search doctors by name
    - /api/doctors/doctors/?specialties=1        - Filter by specialty ID
    - /api/doctors/doctors/?accepting_new_patients=true
    - /api/doctors/doctors/?video_visit_available=true
    - /api/doctors/doctors/?ordering=-average_rating
    - /api/doctors/doctors/search/?specialty=1&min_rating=4&city=Boston&language=Spanish

    - /api/doctors/clinics/?city=Boston          - Filter clinics by city
    - /api/doctors/clinics/?accepts_medicaid=true
    - /api/doctors/clinics/?clinic_type=free_clinic
    - /api/doctors/clinics/nearby/?latitude=42.3601&longitude=-71.0589
"""
