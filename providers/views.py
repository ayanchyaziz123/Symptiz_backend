# ==================== providers/views.py ====================
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Avg
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Specialty, Clinic, Provider, ProviderClinicAffiliation,
    ProviderAvailability, Review
)
from .serializers import (
    SpecialtySerializer, ClinicSerializer, ClinicListSerializer,
    ProviderSerializer, ProviderListSerializer, ProviderDetailSerializer,
    ProviderClinicAffiliationSerializer, ProviderAvailabilitySerializer,
    ReviewSerializer, ReviewCreateSerializer, ProviderRegistrationSerializer
)
from users.models import EmailOTP, User
from users.utils import send_otp_email


class ProviderRegistrationView(APIView):
    """
    Provider registration endpoint with license upload support

    POST /api/providers/register/
    Form data:
    - username, email, password, confirm_password
    - first_name, last_name, phone
    - license_number, license_document (file)
    - years_experience, bio, education, certifications
    - languages, specialty_ids (comma-separated)
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # Convert QueryDict to regular dict, unwrapping single values
        data = {}
        for key, value in request.data.items():
            # QueryDict stores values as lists, unwrap single values
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]
            else:
                data[key] = value

        # Handle specialty_ids - convert from comma-separated string to list of integers
        if 'specialty_ids' in data:
            specialty_ids = data.get('specialty_ids')
            if isinstance(specialty_ids, str):
                data['specialty_ids'] = [int(id.strip()) for id in specialty_ids.split(',') if id.strip()]

        # Check if user already exists (professional UX handling)
        email = data.get('email')
        if email:
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                # If already verified → block registration
                if existing_user.is_email_verified:
                    return Response({
                        'error': 'An account with this email already exists. Please login.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # If not verified → resend OTP and allow re-verification
                otp_obj = EmailOTP.generate_otp(
                    user=existing_user,
                    email=email,
                    purpose='registration',
                    validity_minutes=10
                )

                send_otp_email(
                    email=email,
                    otp=otp_obj.otp,
                    purpose='registration',
                    user_name=existing_user.first_name or existing_user.username
                )

                return Response({
                    'message': 'Email already registered but not verified. A new OTP has been sent to your email.',
                    'user_id': existing_user.id,
                    'email': email,
                    'otp_expires_in_minutes': 10,
                    'next_step': 'Verify OTP at /api/users/auth/verify-otp/'
                }, status=status.HTTP_200_OK)

        serializer = ProviderRegistrationSerializer(data=data)

        if serializer.is_valid():
            result = serializer.save()
            user = result['user']
            provider = result['provider']

            # Generate OTP for email verification
            otp_obj = EmailOTP.generate_otp(
                user=user,
                email=user.email,
                purpose='registration',
                validity_minutes=10
            )

            # Send OTP email
            email_sent = send_otp_email(
                email=user.email,
                otp=otp_obj.otp,
                purpose='registration',
                user_name=user.first_name or user.username
            )

            if not email_sent:
                return Response({
                    'error': 'Failed to send OTP email. Please try again.',
                    'user_id': user.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'message': 'Provider registration successful! Please verify your email.',
                'user_id': user.id,
                'provider_id': provider.id,
                'email': user.email,
                'verification_status': provider.verification_status,
                'otp_sent': True,
                'otp_expires_in_minutes': 10,
                'next_step': 'Verify OTP at /api/users/auth/verify-otp/'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class ProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider operations.
    Supports searching, filtering by specialty, rating, availability, etc.
    """
    queryset = Provider.objects.select_related('user').prefetch_related(
        'specialties', 'clinics', 'providerclinicaffiliation_set__clinic'
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
            return ProviderListSerializer
        elif self.action == 'retrieve':
            return ProviderDetailSerializer
        return ProviderSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for providers with multiple filters"""
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
        """Get all reviews for a specific provider"""
        provider = self.get_object()
        reviews = provider.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability schedule for a specific provider"""
        provider = self.get_object()
        availability = provider.availability.filter(is_active=True)
        serializer = ProviderAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        """Get recommended providers based on user's health profile or symptoms"""
        # This is a placeholder - you would implement logic based on user symptoms
        queryset = self.queryset.filter(
            is_verified=True,
            accepting_new_patients=True
        ).order_by('-average_rating')[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProviderClinicAffiliationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider-clinic relationships.
    """
    queryset = ProviderClinicAffiliation.objects.select_related('provider', 'clinic')
    serializer_class = ProviderClinicAffiliationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'clinic', 'is_primary']

    @action(detail=False, methods=['get'])
    def by_provider(self, request):
        """Get all clinic affiliations for a specific provider"""
        provider_id = request.query_params.get('provider_id')
        if not provider_id:
            return Response(
                {'error': 'provider_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        affiliations = self.queryset.filter(provider_id=provider_id)
        serializer = self.get_serializer(affiliations, many=True)
        return Response(serializer.data)


class ProviderAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider availability schedules.
    """
    queryset = ProviderAvailability.objects.select_related('provider', 'clinic')
    serializer_class = ProviderAvailabilitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'clinic', 'day_of_week', 'is_active']
    ordering = ['day_of_week', 'start_time']

    @action(detail=False, methods=['get'])
    def by_provider(self, request):
        """Get availability for a specific provider"""
        provider_id = request.query_params.get('provider_id')
        if not provider_id:
            return Response(
                {'error': 'provider_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        availability = self.queryset.filter(
            provider_id=provider_id,
            is_active=True
        )
        serializer = self.get_serializer(availability, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider reviews.
    Patients can create, view, update and delete their reviews.
    """
    queryset = Review.objects.select_related('provider', 'patient')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider', 'rating', 'would_recommend']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Automatically set the patient to current user"""
        review = serializer.save(patient=self.request.user)

        # Update provider's average rating and total reviews
        provider = review.provider
        reviews = provider.reviews.all()
        provider.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        provider.total_reviews = reviews.count()
        provider.save()

    def perform_update(self, serializer):
        """Update review and recalculate provider's rating"""
        review = serializer.save()

        # Update provider's average rating
        provider = review.provider
        reviews = provider.reviews.all()
        provider.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        provider.save()

    def perform_destroy(self, instance):
        """Delete review and update provider's rating"""
        provider = instance.provider
        instance.delete()

        # Update provider's average rating and total reviews
        reviews = provider.reviews.all()
        provider.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        provider.total_reviews = reviews.count()
        provider.save()

    @action(detail=False, methods=['get'])
    def by_provider(self, request):
        """Get all reviews for a specific provider"""
        provider_id = request.query_params.get('provider_id')
        if not provider_id:
            return Response(
                {'error': 'provider_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviews = self.queryset.filter(provider_id=provider_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_reviews(self, request):
        """Get all reviews written by the current user"""
        reviews = self.queryset.filter(patient=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)