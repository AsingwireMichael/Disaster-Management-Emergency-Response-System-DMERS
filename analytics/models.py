from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class DimDate(models.Model):
    """Date dimension table for time-based analysis."""
    
    date_key = models.DateField(primary_key=True)
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField()
    month_name = models.CharField(max_length=20)
    week_of_year = models.IntegerField()
    day_of_year = models.IntegerField()
    day_of_month = models.IntegerField()
    day_of_week = models.IntegerField()
    day_name = models.CharField(max_length=20)
    is_weekend = models.BooleanField()
    is_holiday = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'dim_date'
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['month', 'day_of_month']),
        ]
    
    def __str__(self):
        return f"{self.date_key} - {self.year}-{self.month:02d}-{self.day_of_month:02d}"


class DimRegion(models.Model):
    """Region dimension table for geographic analysis."""
    
    region_key = models.AutoField(primary_key=True)
    area_code = models.CharField(max_length=10, unique=True)
    area_name = models.CharField(max_length=255)
    region_type = models.CharField(max_length=50, blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)
    area_sq_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    center_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    center_lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    center_location = gis_models.PointField(blank=True, null=True)
    
    class Meta:
        db_table = 'dim_region'
        indexes = [
            models.Index(fields=['area_code']),
            models.Index(fields=['area_name']),
        ]
    
    def __str__(self):
        return f"{self.area_name} ({self.area_code})"


class DimIncident(models.Model):
    """Incident dimension table for incident analysis."""
    
    incident_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_id = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20)
    severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    status = models.CharField(max_length=20)
    priority_score = models.FloatField()
    
    # Location attributes
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    location = gis_models.PointField(blank=True, null=True)
    
    # Time attributes
    created_date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='incidents_created')
    resolved_date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='incidents_resolved', blank=True, null=True)
    
    # Reporter attributes
    reporter_role = models.CharField(max_length=20)
    reporter_area = models.CharField(max_length=10)
    
    class Meta:
        db_table = 'dim_incident'
        indexes = [
            models.Index(fields=['category', 'severity']),
            models.Index(fields=['status', 'created_date_key']),
            models.Index(fields=['reporter_role', 'created_date_key']),
        ]
    
    def __str__(self):
        return f"{self.incident_id} - {self.category} (Severity: {self.severity})"


class DimUnit(models.Model):
    """Response unit dimension table for unit analysis."""
    
    unit_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit_id = models.CharField(max_length=50, unique=True)
    unit_name = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=20)
    home_area = models.CharField(max_length=255)
    capacity = models.IntegerField()
    
    class Meta:
        db_table = 'dim_unit'
        indexes = [
            models.Index(fields=['unit_type', 'home_area']),
            models.Index(fields=['unit_name']),
        ]
    
    def __str__(self):
        return f"{self.unit_name} ({self.unit_type})"


class FactIncidentDaily(models.Model):
    """Daily incident facts for trend analysis."""
    
    fact_key = models.AutoField(primary_key=True)
    date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='daily_incidents')
    region_key = models.ForeignKey(DimRegion, on_delete=models.CASCADE, related_name='daily_incidents')
    
    # Incident counts
    total_incidents = models.IntegerField(default=0)
    new_incidents = models.IntegerField(default=0)
    resolved_incidents = models.IntegerField(default=0)
    closed_incidents = models.IntegerField(default=0)
    
    # Incident metrics
    avg_severity = models.FloatField(default=0.0)
    max_severity = models.IntegerField(default=0)
    min_severity = models.IntegerField(default=0)
    
    # Category breakdown
    fire_incidents = models.IntegerField(default=0)
    flood_incidents = models.IntegerField(default=0)
    accident_incidents = models.IntegerField(default=0)
    violence_incidents = models.IntegerField(default=0)
    medical_incidents = models.IntegerField(default=0)
    natural_incidents = models.IntegerField(default=0)
    other_incidents = models.IntegerField(default=0)
    
    # Response metrics
    avg_response_time_minutes = models.FloatField(default=0.0)
    total_response_time_minutes = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'fact_incident_daily'
        unique_together = ['date_key', 'region_key']
        indexes = [
            models.Index(fields=['date_key', 'region_key']),
            models.Index(fields=['date_key']),
            models.Index(fields=['region_key']),
        ]
    
    def __str__(self):
        return f"{self.date_key} - {self.region_key.area_name}: {self.total_incidents} incidents"


class FactResponse(models.Model):
    """Response unit performance facts."""
    
    fact_key = models.AutoField(primary_key=True)
    date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='response_facts')
    incident_key = models.ForeignKey(DimIncident, on_delete=models.CASCADE, related_name='response_facts')
    unit_key = models.ForeignKey(DimUnit, on_delete=models.CASCADE, related_name='response_facts')
    region_key = models.ForeignKey(DimRegion, on_delete=models.CASCADE, related_name='response_facts')
    
    # Response timing
    dispatch_time_minutes = models.FloatField(blank=True, null=True)  # Time from incident to dispatch
    response_time_minutes = models.FloatField(blank=True, null=True)  # Time from dispatch to arrival
    on_scene_time_minutes = models.FloatField(blank=True, null=True)  # Time spent on scene
    total_response_time_minutes = models.FloatField(blank=True, null=True)  # Total time from incident to completion
    
    # Response outcomes
    outcome = models.CharField(max_length=20, blank=True, null=True)
    casualties = models.IntegerField(default=0)
    fatalities = models.IntegerField(default=0)
    
    # Unit performance
    unit_distance_km = models.FloatField(blank=True, null=True)  # Distance traveled
    unit_utilization_hours = models.FloatField(default=0.0)  # Hours of unit utilization
    
    class Meta:
        db_table = 'fact_response'
        indexes = [
            models.Index(fields=['date_key', 'region_key']),
            models.Index(fields=['incident_key']),
            models.Index(fields=['unit_key']),
            models.Index(fields=['outcome', 'date_key']),
        ]
    
    def __str__(self):
        return f"Response: {self.unit_key.unit_name} → {self.incident_key.incident_id}"


class FactShelterUtilization(models.Model):
    """Shelter utilization facts for capacity planning."""
    
    fact_key = models.AutoField(primary_key=True)
    date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='shelter_facts')
    region_key = models.ForeignKey(DimRegion, on_delete=models.CASCADE, related_name='shelter_facts')
    
    # Shelter metrics
    total_shelters = models.IntegerField(default=0)
    active_shelters = models.IntegerField(default=0)
    total_capacity = models.IntegerField(default=0)
    total_occupancy = models.IntegerField(default=0)
    avg_occupancy_rate = models.FloatField(default=0.0)
    
    # Shelter types
    emergency_shelters = models.IntegerField(default=0)
    temporary_shelters = models.IntegerField(default=0)
    medical_shelters = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'fact_shelter_utilization'
        unique_together = ['date_key', 'region_key']
        indexes = [
            models.Index(fields=['date_key', 'region_key']),
            models.Index(fields=['date_key']),
        ]
    
    def __str__(self):
        return f"{self.date_key} - {self.region_key.area_name}: {self.avg_occupancy_rate:.1f}% occupancy"


class FactInventory(models.Model):
    """Inventory and supply chain facts."""
    
    fact_key = models.AutoField(primary_key=True)
    date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, related_name='inventory_facts')
    region_key = models.ForeignKey(DimRegion, on_delete=models.CASCADE, related_name='inventory_facts')
    
    # Inventory metrics
    total_items = models.IntegerField(default=0)
    low_stock_items = models.IntegerField(default=0)
    out_of_stock_items = models.IntegerField(default=0)
    
    # Category breakdown
    food_water_items = models.IntegerField(default=0)
    medical_items = models.IntegerField(default=0)
    hygiene_items = models.IntegerField(default=0)
    clothing_items = models.IntegerField(default=0)
    tool_items = models.IntegerField(default=0)
    
    # Supply chain metrics
    items_distributed = models.IntegerField(default=0)
    items_restocked = models.IntegerField(default=0)
    items_expired = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'fact_inventory'
        unique_together = ['date_key', 'region_key']
        indexes = [
            models.Index(fields=['date_key', 'region_key']),
            models.Index(fields=['date_key']),
        ]
    
    def __str__(self):
        return f"{self.date_key} - {self.region_key.area_name}: {self.total_items} items"
