from django.urls import path
from .views import (
    SymptomCategoryViewSet,
    SymptomCheckViewSet,
    HealthTipViewSet
)

urlpatterns = [
    # ===== SYMPTOM CATEGORIES =====
    
    # List and create categories
    path('categories/', 
         SymptomCategoryViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='symptom-category-list'),
    
    # Category detail operations
    path('categories/<int:pk>/', 
         SymptomCategoryViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='symptom-category-detail'),
    
    
    # ===== SYMPTOM CHECKS (AI-POWERED) =====

    # Conversational symptom analysis - Start conversation
    path('checks/start_conversation/',
         SymptomCheckViewSet.as_view({'post': 'start_conversation'}),
         name='symptom-check-start-conversation'),

    # Conversational symptom analysis - Continue conversation
    path('checks/continue_conversation/',
         SymptomCheckViewSet.as_view({'post': 'continue_conversation'}),
         name='symptom-check-continue-conversation'),

    # Quick analysis without saving (main endpoint for frontend)
    path('checks/analyze/',
         SymptomCheckViewSet.as_view({'post': 'analyze'}),
         name='symptom-check-analyze'),

    # User's symptom history
    path('checks/my-history/',
         SymptomCheckViewSet.as_view({'get': 'my_history'}),
         name='symptom-check-my-history'),
    
    # Statistics (admin only)
    path('checks/statistics/', 
         SymptomCheckViewSet.as_view({'get': 'statistics'}), 
         name='symptom-check-statistics'),
    
    # List and create symptom checks
    path('checks/', 
         SymptomCheckViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='symptom-check-list'),
    
    # Mark appointment booked for specific check
    path('checks/<int:pk>/book-appointment/', 
         SymptomCheckViewSet.as_view({'post': 'book_appointment'}), 
         name='symptom-check-book-appointment'),
    
    # Symptom check detail operations
    path('checks/<int:pk>/', 
         SymptomCheckViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='symptom-check-detail'),
    
    
    # ===== HEALTH TIPS =====
    
    # Random health tips
    path('health-tips/random/', 
         HealthTipViewSet.as_view({'get': 'random'}), 
         name='health-tip-random'),
    
    # Daily health tip
    path('health-tips/daily-tip/', 
         HealthTipViewSet.as_view({'get': 'daily_tip'}), 
         name='health-tip-daily'),
    
    # Tips by category
    path('health-tips/by-category/', 
         HealthTipViewSet.as_view({'get': 'by_category'}), 
         name='health-tip-by-category'),
    
    # List and create health tips
    path('health-tips/', 
         HealthTipViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='health-tip-list'),
    
    # Health tip detail operations
    path('health-tips/<int:pk>/', 
         HealthTipViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='health-tip-detail'),
]