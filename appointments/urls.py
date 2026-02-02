# ==================== appointments/urls.py ====================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AppointmentReminderViewSet

# Router for ViewSets
router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'reminders', AppointmentReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
]

# Available endpoints:
# GET    /api/appointments/appointments/              - List appointments (filtered by user)
# POST   /api/appointments/appointments/              - Create new appointment
# GET    /api/appointments/appointments/{id}/         - Retrieve appointment details
# PUT    /api/appointments/appointments/{id}/         - Update appointment
# PATCH  /api/appointments/appointments/{id}/         - Partial update
# DELETE /api/appointments/appointments/{id}/         - Delete appointment
#
# Custom actions:
# GET    /api/appointments/appointments/upcoming/     - Get upcoming appointments
# GET    /api/appointments/appointments/past/         - Get past appointments
# GET    /api/appointments/appointments/today/        - Get today's appointments
# POST   /api/appointments/appointments/{id}/confirm/ - Confirm appointment
# POST   /api/appointments/appointments/{id}/cancel/  - Cancel appointment
# POST   /api/appointments/appointments/{id}/complete/ - Mark as completed (doctors)
# POST   /api/appointments/appointments/{id}/reschedule/ - Reschedule appointment
# GET    /api/appointments/appointments/available_slots/ - Get available time slots
# GET    /api/appointments/appointments/statistics/   - Get appointment statistics
#
# Reminders:
# GET    /api/appointments/reminders/                 - List reminders
# GET    /api/appointments/reminders/{id}/            - Reminder details
