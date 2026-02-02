# ==================== users/admin.py ====================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

admin.site.register(User)
# class UserAdmin(BaseUserAdmin):
#     list_display = ('username', 'email', 'user_type', 'phone', 'created_at')
#     list_filter = ('user_type', 'is_staff', 'is_active')
#     search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    
#     fieldsets = BaseUserAdmin.fieldsets + (
#         ('Additional Info', {
#             'fields': ('user_type', 'phone', 'date_of_birth', 'profile_picture')
#         }),
#         ('Address', {
#             'fields': ('address', 'city', 'state', 'zip_code')
#         }),
#         ('Insurance', {
#             'fields': ('insurance_provider', 'insurance_id')
#         }),
#         ('Emergency Contact', {
#             'fields': ('emergency_contact_name', 'emergency_contact_phone')
#         }),
#         ('Preferences', {
#             'fields': ('email_reminders', 'sms_reminders')
#         }),
#     )