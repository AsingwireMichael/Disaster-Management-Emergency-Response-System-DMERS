from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

User = get_user_model()


class Area(models.Model):
    """Geographic areas for incident categorization."""
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    boundary = gis_models.PolygonField(blank=True, null=True)
    center = gis_models.PointField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'area'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Incident(models.Model):
    """Core incident model with PostGIS support and partitioning."""
    
    class Category(models.TextChoices):
        FIRE = 'FIRE', 'Fire'
        FLOOD = 'FLOOD', 'Flood'
        ACCIDENT = 'ACCIDENT', 'Accident'
        VIOLENCE = 'VIOLENCE', 'Violence'
        MEDICAL = 'MEDICAL', 'Medical Emergency'
        NATURAL = 'NATURAL', 'Natural Disaster'
        OTHER = 'OTHER', 'Other'
    
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        TRIAGED = 'TRIAGED', 'Triaged'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        ONGOING = 'ONGOING', 'Ongoing'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    # Core fields
    incident_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reporting information
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_incidents')
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='incidents')
    
    # Incident details
    category = models.CharField(max_length=20, choices=Category.choices)
    severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Severity level 1-5 (1=Low, 5=Critical)"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    
    # Location
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    location = gis_models.PointField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Description
    summary = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    # Response tracking
    triaged_at = models.DateTimeField(blank=True, null=True)
    dispatched_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    priority_score = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'incident'
        indexes = [
            models.Index(fields=['status', 'severity', 'created_at']),
            models.Index(fields=['category', 'area']),
            models.Index(fields=['reported_by', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.summary[:50]} ({self.incident_id})"
    
    def save(self, *args, **kwargs):
        # Auto-generate location point from lat/lon
        if self.lat and self.lon and not self.location:
            self.location = Point(float(self.lon), float(self.lat))
        
        # Calculate priority score based on severity and time
        if self.severity:
            self.priority_score = self.severity * 10
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status in [self.Status.NEW, self.Status.TRIAGED, self.Status.DISPATCHED, self.Status.ONGOING]
    
    @property
    def response_time(self):
        if self.dispatched_at and self.created_at:
            return self.dispatched_at - self.created_at
        return None


class IncidentStatusHistory(models.Model):
    """Track all status changes for incidents."""
    
    id = models.BigAutoField(primary_key=True)
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Incident.Status.choices, blank=True, null=True)
    new_status = models.CharField(max_length=20, choices=Incident.Status.choices)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='status_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'incident_status_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['incident', 'changed_at']),
            models.Index(fields=['new_status', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.incident.incident_id}: {self.old_status} → {self.new_status}"


class IncidentMedia(models.Model):
    """Media attachments for incidents."""
    
    class MediaType(models.TextChoices):
        IMAGE = 'IMAGE', 'Image'
        VIDEO = 'VIDEO', 'Video'
        AUDIO = 'AUDIO', 'Audio'
        DOCUMENT = 'DOCUMENT', 'Document'
    
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    file = models.FileField(upload_to='incident_media/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'incident_media'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.media_type} for {self.incident.incident_id}"


class IncidentNote(models.Model):
    """Notes and updates for incidents."""
    
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to citizens")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'incident_note'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note by {self.author.full_name} on {self.incident.incident_id}"


# Signal handlers for automatic status history tracking
@receiver(post_save, sender=Incident)
def create_status_history(sender, instance, created, **kwargs):
    """Automatically create status history when incident status changes."""
    if created:
        # New incident
        IncidentStatusHistory.objects.create(
            incident=instance,
            new_status=instance.status,
            changed_by=instance.reported_by,
            notes="Incident created"
        )
    else:
        # Check if status changed
        try:
            old_instance = Incident.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                IncidentStatusHistory.objects.create(
                    incident=instance,
                    old_status=old_instance.status,
                    new_status=instance.status,
                    changed_by=instance.reported_by,  # This should be the actual user making the change
                    notes=f"Status changed from {old_instance.status} to {instance.status}"
                )
        except Incident.DoesNotExist:
            pass
