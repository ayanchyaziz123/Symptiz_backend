# ==================== doctors/views.py ====================
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Q, Avg
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Specialty, Clinic, Doctor, DoctorClinicAffiliation,
    DoctorAvailability, Review
)
from .serializers import (
    SpecialtySerializer, ClinicSerializer, ClinicListSerializer,
    DoctorSerializer, DoctorListSerializer, DoctorDetailSerializer,
    DoctorClinicAffiliationSerializer, DoctorAvailabilitySerializer,
    ReviewSerializer, ReviewCreateSerializer
)


class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing specialties.
    List and detail views only - specialties are managed via admin.
    """
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class ClinicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for clinic operations.
    List, retrieve, create, update, delete clinics.
    Supports filtering by location, type, and affordability options.
    """
    queryset = Clinic.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city', 'state', 'address']
    filterset_fields = [
        'city', 'state', 'clinic_type', 'accepts_medicaid',
        'accepts_medicare', 'sliding_scale', 'free_services'
    ]
    ordering_fields = ['name', 'city', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClinicListSerializer
        return ClinicSerializer

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find clinics near user location"""
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')

        if not lat or not lon:
            return Response(
                {'error': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # This is a simple filter - for production, use PostGIS for proper distance calculation
        clinics = self.queryset.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )

        serializer = self.get_serializer(clinics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def affordable(self, request):
        """Get affordable clinic options"""
        clinics = self.queryset.filter(
            Q(accepts_medicaid=True) |
            Q(accepts_medicare=True) |
            Q(sliding_scale=True) |
            Q(free_services=True)
        ).distinct()

        serializer = self.get_serializer(clinics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Get list of unique cities with clinics"""
        cities = self.queryset.values('city', 'state').distinct().order_by('city')
        city_list = [f"{city['city']}, {city['state']}" for city in cities]
        return Response({'cities': city_list})


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for doctor operations.
    Supports searching, filtering by specialty, rating, availability, etc.
    """
    queryset = Doctor.objects.select_related('user').prefetch_related(
        'specialties', 'clinics', 'doctorclinicaffiliation_set__clinic'
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'bio', 'languages']
    filterset_fields = [
        'accepting_new_patients', 'video_visit_available',
        'is_verified', 'specialties'
    ]
    ordering_fields = ['average_rating', 'years_experience', 'created_at']
    ordering = ['-average_rating']

    def get_serializer_class(self):
        if self.action == 'list':
            return DoctorListSerializer
        elif self.action == 'retrieve':
            return DoctorDetailSerializer
        return DoctorSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for doctors with multiple filters"""
        queryset = self.queryset

        # Filter by specialty
        specialty = request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialties__id=specialty)

        # Filter by minimum rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))

        # Filter by languages
        language = request.query_params.get('language')
        if language:
            queryset = queryset.filter(languages__icontains=language)

        # Filter by city (through clinics)
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(clinics__city__iexact=city).distinct()

        # Filter by accepting new patients
        accepting_new = request.query_params.get('accepting_new_patients')
        if accepting_new and accepting_new.lower() == 'true':
            queryset = queryset.filter(accepting_new_patients=True)

        # Filter by video visits
        video_visit = request.query_params.get('video_visit')
        if video_visit and video_visit.lower() == 'true':
            queryset = queryset.filter(video_visit_available=True)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a specific doctor"""
        doctor = self.get_object()
        reviews = doctor.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability schedule for a specific doctor"""
        doctor = self.get_object()
        availability = doctor.availability.filter(is_active=True)
        serializer = DoctorAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        """Get recommended doctors based on user's health profile or symptoms"""
        # This is a placeholder - you would implement logic based on user symptoms
        queryset = self.queryset.filter(
            is_verified=True,
            accepting_new_patients=True
        ).order_by('-average_rating')[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DoctorClinicAffiliationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor-clinic relationships.
    """
    queryset = DoctorClinicAffiliation.objects.select_related('doctor', 'clinic')
    serializer_class = DoctorClinicAffiliationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doctor', 'clinic', 'is_primary']

    @action(detail=False, methods=['get'])
    def by_doctor(self, request):
        """Get all clinic affiliations for a specific doctor"""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response(
                {'error': 'doctor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        affiliations = self.queryset.filter(doctor_id=doctor_id)
        serializer = self.get_serializer(affiliations, many=True)
        return Response(serializer.data)


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor availability schedules.
    """
    queryset = DoctorAvailability.objects.select_related('doctor', 'clinic')
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doctor', 'clinic', 'day_of_week', 'is_active']
    ordering = ['day_of_week', 'start_time']

    @action(detail=False, methods=['get'])
    def by_doctor(self, request):
        """Get availability for a specific doctor"""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response(
                {'error': 'doctor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        availability = self.queryset.filter(
            doctor_id=doctor_id,
            is_active=True
        )
        serializer = self.get_serializer(availability, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor reviews.
    Patients can create, view, update and delete their reviews.
    """
    queryset = Review.objects.select_related('doctor', 'patient')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['doctor', 'rating', 'would_recommend']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Automatically set the patient to current user"""
        review = serializer.save(patient=self.request.user)

        # Update doctor's average rating and total reviews
        doctor = review.doctor
        reviews = doctor.reviews.all()
        doctor.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        doctor.total_reviews = reviews.count()
        doctor.save()

    def perform_update(self, serializer):
        """Update review and recalculate doctor's rating"""
        review = serializer.save()

        # Update doctor's average rating
        doctor = review.doctor
        reviews = doctor.reviews.all()
        doctor.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        doctor.save()

    def perform_destroy(self, instance):
        """Delete review and update doctor's rating"""
        doctor = instance.doctor
        instance.delete()

        # Update doctor's average rating and total reviews
        reviews = doctor.reviews.all()
        doctor.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        doctor.total_reviews = reviews.count()
        doctor.save()

    @action(detail=False, methods=['get'])
    def by_doctor(self, request):
        """Get all reviews for a specific doctor"""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response(
                {'error': 'doctor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviews = self.queryset.filter(doctor_id=doctor_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_reviews(self, request):
        """Get all reviews written by the current user"""
        reviews = self.queryset.filter(patient=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
