from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from incidents.models import Incident
import uuid
from django.utils import timezone

User = get_user_model()


class ResponderUnit(models.Model):
    """Emergency response unit (ambulance, fire truck, police, etc.)."""
    
    class UnitType(models.TextChoices):
        AMBULANCE = 'AMBULANCE', 'Ambulance'
        FIRE_TRUCK = 'FIRE_TRUCK', 'Fire Truck'
        POLICE = 'POLICE', 'Police Vehicle'
        RESCUE = 'RESCUE', 'Rescue Vehicle'
        NGO_TEAM = 'NGO_TEAM', 'NGO Team'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer Team'
        OTHER = 'OTHER', 'Other'
    
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        ON_SCENE = 'ON_SCENE', 'On Scene'
        RETURNING = 'RETURNING', 'Returning to Base'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        OFFLINE = 'OFFLINE', 'Offline'
    
    # Core fields
    unit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=20, choices=UnitType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    
    # Location and area
    home_area = models.CharField(max_length=255)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_location = gis_models.PointField(blank=True, null=True)
    
    # Capacity and capabilities
    capacity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    current_occupancy = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    capabilities = models.JSONField(default=list, blank=True)  # List of capabilities
    equipment = models.JSONField(default=list, blank=True)     # List of equipment
    
    # Contact and operational info
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    radio_channel = models.CharField(max_length=20, blank=True, null=True)
    base_station = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_status_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'responder_unit'
        indexes = [
            models.Index(fields=['unit_type', 'status']),
            models.Index(fields=['home_area', 'status']),
            models.Index(fields=['status', 'last_status_update']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()}) - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate location point from lat/lon
        if self.current_lat and self.current_lon and not self.current_location:
            self.current_location = Point(float(self.current_lon), float(self.current_lat))
        
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE
    
    @property
    def is_operational(self):
        return self.status not in [self.Status.MAINTENANCE, self.Status.OFFLINE]


class ResponderAssignment(models.Model):
    """Assignment of responders to units."""
    
    responder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unit_assignments')
    unit = models.ForeignKey(ResponderUnit, on_delete=models.CASCADE, related_name='responder_assignments')
    role = models.CharField(max_length=50, blank=True, null=True)  # Driver, Medic, Officer, etc.
    is_primary = models.BooleanField(default=False)  # Primary responder for the unit
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_until = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'responder_assignment'
        unique_together = ['responder', 'unit', 'is_active']
        indexes = [
            models.Index(fields=['responder', 'is_active']),
            models.Index(fields=['unit', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.responder.full_name} → {self.unit.name}"


class Dispatch(models.Model):
    """Dispatch of a responder unit to an incident."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        EN_ROUTE = 'EN_ROUTE', 'En Route'
        ON_SCENE = 'ON_SCENE', 'On Scene'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class Outcome(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        PARTIAL = 'PARTIAL', 'Partial Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        OTHER = 'OTHER', 'Other'
    
    # Core fields
    dispatch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='dispatches')
    unit = models.ForeignKey(ResponderUnit, on_delete=models.CASCADE, related_name='dispatches')
    
    # Status and timing
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    assigned_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    en_route_at = models.DateTimeField(blank=True, null=True)
    arrived_at = models.DateTimeField(blank=True, null=True)
    cleared_at = models.DateTimeField(blank=True, null=True)
    
    # Outcome and notes
    outcome = models.CharField(max_length=20, choices=Outcome.choices, blank=True, null=True)
    outcome_notes = models.TextField(blank=True, null=True)
    
    # Response metrics
    response_time = models.DurationField(blank=True, null=True)  # Time from dispatch to arrival
    on_scene_time = models.DurationField(blank=True, null=True)  # Time spent on scene
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dispatch'
        indexes = [
            models.Index(fields=['status', 'assigned_at']),
            models.Index(fields=['incident', 'status']),
            models.Index(fields=['unit', 'status']),
        ]
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Dispatch {self.dispatch_id}: {self.unit.name} → {self.incident.incident_id}"
    
    def save(self, *args, **kwargs):
        # Calculate response time when arrived
        if self.arrived_at and self.assigned_at and not self.response_time:
            self.response_time = self.arrived_at - self.assigned_at
        
        # Calculate on-scene time when cleared
        if self.cleared_at and self.arrived_at and not self.on_scene_time:
            self.on_scene_time = self.cleared_at - self.arrived_at
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status in [self.Status.PENDING, self.Status.ASSIGNED, self.Status.ACKNOWLEDGED, self.Status.EN_ROUTE, self.Status.ON_SCENE]


class SituationReport(models.Model):
    """Situation reports from responder units."""
    
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE, related_name='situation_reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='situation_reports')
    
    # Report content
    title = models.CharField(max_length=255)
    content = models.TextField()
    assessment = models.TextField(blank=True, null=True)
    
    # Operational details
    casualties = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    fatalities = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    resources_needed = models.JSONField(default=list, blank=True)
    
    # Location and status
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location = gis_models.PointField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'situation_report'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dispatch', 'created_at']),
            models.Index(fields=['reporter', 'created_at']),
        ]
    
    def __str__(self):
        return f"SitRep: {self.title} - {self.dispatch.unit.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate location point from lat/lon
        if self.lat and self.lon and not self.location:
            self.location = Point(float(self.lon), float(self.lat))
        
        super().save(*args, **kwargs)


# Signal handlers for automatic updates
@receiver(post_save, sender=Dispatch)
def update_unit_status_on_dispatch(sender, instance, created, **kwargs):
    """Update responder unit status when dispatch status changes."""
    if created:
        # New dispatch - mark unit as dispatched
        instance.unit.status = ResponderUnit.Status.DISPATCHED
        instance.unit.save()
    else:
        # Status change
        if instance.status == Dispatch.Status.ON_SCENE:
            instance.unit.status = ResponderUnit.Status.ON_SCENE
        elif instance.status == Dispatch.Status.COMPLETED:
            instance.unit.status = ResponderUnit.Status.AVAILABLE
        elif instance.status == Dispatch.Status.CANCELLED:
            instance.unit.status = ResponderUnit.Status.AVAILABLE
        
        instance.unit.save()


@receiver(post_save, sender=ResponderUnit)
def update_unit_location_timestamp(sender, instance, **kwargs):
    """Update last status update timestamp when unit location changes."""
    if 'current_lat' in kwargs.get('update_fields', []) or 'current_lon' in kwargs.get('update_fields', []):
        instance.last_status_update = timezone.now()
        instance.save(update_fields=['last_status_update'])
