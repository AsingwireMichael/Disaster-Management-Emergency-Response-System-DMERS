from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Custom user model for DMERS system."""
    
    class Role(models.TextChoices):
        CITIZEN = 'CITIZEN', 'Citizen'
        RESPONDER = 'RESPONDER', 'Responder'
        COMMAND = 'COMMAND', 'Command Center'
        ADMIN = 'ADMIN', 'Administrator'
    
    # Override username to use email
    username = None
    email = models.EmailField(unique=True)
    
    # User profile fields
    full_name = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN
    )
    is_active = models.BooleanField(default=True)
    
    # Location fields for emergency response
    home_address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone', 'role']
    
    class Meta:
        db_table = 'app_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def is_citizen(self):
        return self.role == self.Role.CITIZEN
    
    @property
    def is_responder(self):
        return self.role == self.Role.RESPONDER
    
    @property
    def is_command(self):
        return self.role == self.Role.COMMAND
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class UserProfile(models.Model):
    """Extended user profile information."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Emergency response specific fields
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True, null=True
    )
    medical_conditions = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    
    # Emergency preferences
    preferred_language = models.CharField(max_length=10, default='en')
    notification_preferences = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profile'
    
    def __str__(self):
        return f"Profile for {self.user.full_name}"
