# ==================== providers/urls.py ====================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SpecialtyViewSet, ClinicViewSet, ProviderViewSet,
    ProviderClinicAffiliationViewSet, ProviderAvailabilityViewSet,
    ReviewViewSet, ProviderRegistrationView
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'specialties', SpecialtyViewSet, basename='specialty')
router.register(r'clinics', ClinicViewSet, basename='clinic')
router.register(r'providers', ProviderViewSet, basename='provider')
router.register(r'affiliations', ProviderClinicAffiliationViewSet, basename='affiliation')
router.register(r'availability', ProviderAvailabilityViewSet, basename='availability')
router.register(r'reviews', ReviewViewSet, basename='review')

app_name = 'providers'

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Provider registration (outside router)
    path('register/', ProviderRegistrationView.as_view(), name='provider-register'),

    # Router URLs
    path('', include(router.urls)),
]

"""
API Endpoints:

Specialties:
    GET    /api/providers/specialties/           - List all specialties
    GET    /api/providers/specialties/{id}/      - Get specialty details

Clinics:
    GET    /api/providers/clinics/               - List all clinics
    POST   /api/providers/clinics/               - Create new clinic
    GET    /api/providers/clinics/{id}/          - Get clinic details
    PUT    /api/providers/clinics/{id}/          - Update clinic
    PATCH  /api/providers/clinics/{id}/          - Partial update clinic
    DELETE /api/providers/clinics/{id}/          - Delete clinic
    GET    /api/providers/clinics/nearby/        - Find nearby clinics (requires latitude & longitude params)
    GET    /api/providers/clinics/affordable/    - Get affordable clinics
    GET    /api/providers/clinics/cities/        - Get list of cities with clinics

Providers:
    GET    /api/providers/providers/               - List all providers
    POST   /api/providers/providers/               - Create new provider
    GET    /api/providers/providers/{id}/          - Get provider details
    PUT    /api/providers/providers/{id}/          - Update provider
    PATCH  /api/providers/providers/{id}/          - Partial update provider
    DELETE /api/providers/providers/{id}/          - Delete provider
    GET    /api/providers/providers/search/        - Advanced provider search
    GET    /api/providers/providers/{id}/reviews/  - Get reviews for specific provider
    GET    /api/providers/providers/{id}/availability/ - Get availability for specific provider
    GET    /api/providers/providers/recommended/   - Get recommended providers (requires auth)

Provider-Clinic Affiliations:
    GET    /api/providers/affiliations/          - List all affiliations
    POST   /api/providers/affiliations/          - Create new affiliation
    GET    /api/providers/affiliations/{id}/     - Get affiliation details
    PUT    /api/providers/affiliations/{id}/     - Update affiliation
    PATCH  /api/providers/affiliations/{id}/     - Partial update affiliation
    DELETE /api/providers/affiliations/{id}/     - Delete affiliation
    GET    /api/providers/affiliations/by_provider/ - Get affiliations by provider (requires provider_id param)

Provider Availability:
    GET    /api/providers/availability/          - List all availability schedules
    POST   /api/providers/availability/          - Create new availability
    GET    /api/providers/availability/{id}/     - Get availability details
    PUT    /api/providers/availability/{id}/     - Update availability
    PATCH  /api/providers/availability/{id}/     - Partial update availability
    DELETE /api/providers/availability/{id}/     - Delete availability
    GET    /api/providers/availability/by_provider/ - Get availability by provider (requires provider_id param)

Reviews:
    GET    /api/providers/reviews/               - List all reviews
    POST   /api/providers/reviews/               - Create new review (requires auth)
    GET    /api/providers/reviews/{id}/          - Get review details
    PUT    /api/providers/reviews/{id}/          - Update review
    PATCH  /api/providers/reviews/{id}/          - Partial update review
    DELETE /api/providers/reviews/{id}/          - Delete review
    GET    /api/providers/reviews/by_provider/   - Get reviews by provider (requires provider_id param)
    GET    /api/providers/reviews/my_reviews/    - Get current user's reviews (requires auth)

Registration:
    POST   /api/providers/register/              - Register new provider with license upload

Search & Filter Examples:
    - /api/providers/providers/?search=john          - Search providers by name
    - /api/providers/providers/?specialties=1        - Filter by specialty ID
    - /api/providers/providers/?accepting_new_patients=true
    - /api/providers/providers/?video_visit_available=true
    - /api/providers/providers/?ordering=-average_rating
    - /api/providers/providers/search/?specialty=1&min_rating=4&city=Boston&language=Spanish

    - /api/providers/clinics/?city=Boston          - Filter clinics by city
    - /api/providers/clinics/?accepts_medicaid=true
    - /api/providers/clinics/?clinic_type=free_clinic
    - /api/providers/clinics/nearby/?latitude=42.3601&longitude=-71.0589
"""