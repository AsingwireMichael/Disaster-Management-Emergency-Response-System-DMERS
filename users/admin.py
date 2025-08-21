from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = ('email', 'full_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone', 'role', 'home_address')}),
        ('Emergency Contacts', {'fields': ('emergency_contact', 'emergency_contact_phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    
    list_display = ('user', 'blood_type', 'preferred_language', 'created_at')
    list_filter = ('blood_type', 'preferred_language', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Medical Information', {'fields': ('blood_type', 'medical_conditions', 'allergies', 'medications')}),
        ('Preferences', {'fields': ('preferred_language', 'notification_preferences')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
