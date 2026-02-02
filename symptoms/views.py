from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import SymptomCategory, SymptomCheck, HealthTip
from .serializers import (
    SymptomCategorySerializer, SymptomCheckSerializer,
    SymptomCheckCreateSerializer, SymptomCheckListSerializer,
    HealthTipSerializer, HealthTipListSerializer
)
from .ai_service import symptom_analyzer, doctor_recommender


class SymptomCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SymptomCategory CRUD operations
    """
    queryset = SymptomCategory.objects.all()
    serializer_class = SymptomCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']


class SymptomCheckViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SymptomCheck operations with AI-powered analysis
    Allows anonymous users to check symptoms
    """
    queryset = SymptomCheck.objects.select_related('patient')
    serializer_class = SymptomCheckSerializer
    permission_classes = [permissions.AllowAny]  # Allow anonymous checks
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['urgency_level', 'follow_up_needed', 'appointment_booked']
    ordering_fields = ['created_at', 'urgency_level']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter queryset based on user authentication
        Authenticated users see only their checks, anonymous users see nothing
        """
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return SymptomCheck.objects.all()
            return SymptomCheck.objects.filter(patient=self.request.user)
        
        # Anonymous users can create but not list
        return SymptomCheck.objects.none()
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return SymptomCheckCreateSerializer
        elif self.action == 'list':
            return SymptomCheckListSerializer
        return SymptomCheckSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create symptom check with AI analysis
        This endpoint automatically analyzes symptoms using AI
        """
        symptoms = request.data.get('symptoms_description', '')
        
        if not symptoms or len(symptoms.strip()) < 10:
            return Response(
                {'error': 'Please provide a detailed description of your symptoms (at least 10 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # AI Analysis
        try:
            analysis_result = symptom_analyzer.analyze_symptoms(symptoms)
            
            # Get recommended specialties
            specialties = doctor_recommender.get_recommended_specialties(
                symptoms, 
                analysis_result['urgency_level']
            )
            analysis_result['recommended_specialties'] = specialties
            
        except Exception as e:
            return Response(
                {'error': f'AI analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create symptom check record
        serializer = self.get_serializer(
            data=analysis_result,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        symptom_check = serializer.save()
        
        # Return full details including AI recommendations
        output_serializer = SymptomCheckSerializer(symptom_check)
        response_data = output_serializer.data
        response_data['recommended_specialties'] = specialties
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def analyze(self, request):
        """
        Quick symptom analysis endpoint without saving to database
        Use this for instant feedback before user decides to save
        
        POST /api/symptoms/checks/analyze/
        Body: { "symptoms": "your symptoms description" }
        """
        symptoms = request.data.get('symptoms', '') or request.data.get('symptoms_description', '')
        
        if not symptoms or len(symptoms.strip()) < 10:
            return Response(
                {'error': 'Please provide a detailed description of your symptoms (at least 10 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Run AI analysis
            analysis = symptom_analyzer.analyze_symptoms(symptoms)
            
            # Get recommended specialties
            specialties = doctor_recommender.get_recommended_specialties(
                symptoms,
                analysis['urgency_level']
            )
            
            # Format response for frontend
            import json
            response_data = {
                'urgency': analysis['urgency_level'],
                'recommendation': analysis['recommendation'],
                'provider_type': analysis['recommended_provider_type'],
                'confidence': float(analysis['confidence_score']),
                'possible_conditions': json.loads(analysis.get('possible_conditions', '[]')),
                'recommended_specialties': specialties,
                'follow_up_needed': analysis['follow_up_needed']
            }
            
            return Response(response_data)
            
        except Exception as e:
            import traceback
            print(f"Analysis error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def book_appointment(self, request, pk=None):
        """Mark that user has booked appointment for this symptom check"""
        symptom_check = self.get_object()
        symptom_check.appointment_booked = True
        symptom_check.save()
        
        serializer = self.get_serializer(symptom_check)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get symptom check statistics (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = SymptomCheck.objects.all()
        
        stats = {
            'total_checks': queryset.count(),
            'emergency': queryset.filter(urgency_level='emergency').count(),
            'doctor_visit': queryset.filter(urgency_level='doctor_visit').count(),
            'home_care': queryset.filter(urgency_level='home_care').count(),
            'appointments_booked': queryset.filter(appointment_booked=True).count(),
            'follow_up_needed': queryset.filter(follow_up_needed=True).count()
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def my_history(self, request):
        """Get current user's symptom check history"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        checks = SymptomCheck.objects.filter(patient=request.user).order_by('-created_at')[:10]
        serializer = SymptomCheckListSerializer(checks, many=True)
        return Response(serializer.data)


class HealthTipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for HealthTip CRUD operations
    """
    queryset = HealthTip.objects.select_related('category')
    serializer_class = HealthTipSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show active tips to non-staff users"""
        if self.request.user.is_staff:
            return HealthTip.objects.all()
        return HealthTip.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        """Use simplified serializer for list view"""
        if self.action == 'list':
            return HealthTipListSerializer
        return HealthTipSerializer
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """Get random health tips"""
        count = int(request.query_params.get('count', 5))
        tips = self.get_queryset().order_by('?')[:count]
        serializer = self.get_serializer(tips, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get health tips grouped by category"""
        category_id = request.query_params.get('category_id')
        
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tips = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(tips, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def daily_tip(self, request):
        """Get daily health tip (could be cached)"""
        from datetime import date
        
        # Use date as seed for consistent daily tip
        today = date.today()
        tip_count = self.get_queryset().count()
        
        if tip_count == 0:
            return Response(
                {'message': 'No health tips available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tip_index = today.toordinal() % tip_count
        tip = self.get_queryset()[tip_index:tip_index + 1].first()
        
        if tip:
            serializer = self.get_serializer(tip)
            return Response(serializer.data)
        
        return Response(
            {'message': 'No health tips available'},
            status=status.HTTP_404_NOT_FOUND
        )