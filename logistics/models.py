from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from incidents.models import Area
import uuid


class Shelter(models.Model):
    """Emergency shelter locations."""
    
    class ShelterType(models.TextChoices):
        EMERGENCY = 'EMERGENCY', 'Emergency Shelter'
        TEMPORARY = 'TEMPORARY', 'Temporary Shelter'
        PERMANENT = 'PERMANENT', 'Permanent Shelter'
        MEDICAL = 'MEDICAL', 'Medical Shelter'
        CHILDREN = 'CHILDREN', 'Children\'s Shelter'
        ANIMAL = 'ANIMAL', 'Animal Shelter'
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        STANDBY = 'STANDBY', 'Standby'
        FULL = 'FULL', 'At Capacity'
        CLOSED = 'CLOSED', 'Closed'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    
    # Core fields
    shelter_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    shelter_type = models.CharField(max_length=20, choices=ShelterType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STANDBY)
    
    # Location
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='shelters')
    address = models.TextField()
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    location = gis_models.PointField(blank=True, null=True)
    
    # Capacity and occupancy
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    current_occupancy = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    max_occupancy = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Facilities and services
    facilities = models.JSONField(default=list, blank=True)  # List of available facilities
    services = models.JSONField(default=list, blank=True)    # List of available services
    accessibility = models.JSONField(default=list, blank=True)  # Accessibility features
    
    # Contact and operational info
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    manager_name = models.CharField(max_length=255, blank=True, null=True)
    manager_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Operational details
    open_24_7 = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shelter'
        indexes = [
            models.Index(fields=['shelter_type', 'status']),
            models.Index(fields=['area', 'status']),
            models.Index(fields=['status', 'current_occupancy']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_shelter_type_display()}) - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate location point from lat/lon
        if self.lat and self.lon and not self.location:
            self.location = Point(float(self.lon), float(self.lat))
        
        # Update status based on occupancy
        if self.current_occupancy >= self.max_occupancy:
            self.status = self.Status.FULL
        elif self.current_occupancy > 0:
            self.status = self.Status.ACTIVE
        elif self.status == self.Status.FULL:
            self.status = self.Status.ACTIVE
        
        super().save(*args, **kwargs)
    
    @property
    def available_capacity(self):
        return max(0, self.max_occupancy - self.current_occupancy)
    
    @property
    def occupancy_percentage(self):
        if self.max_occupancy > 0:
            return (self.current_occupancy / self.max_occupancy) * 100
        return 0


class Item(models.Model):
    """Inventory items for shelters and emergency response."""
    
    class Category(models.TextChoices):
        FOOD = 'FOOD', 'Food & Water'
        MEDICAL = 'MEDICAL', 'Medical Supplies'
        HYGIENE = 'HYGIENE', 'Hygiene Items'
        CLOTHING = 'CLOTHING', 'Clothing & Bedding'
        TOOLS = 'TOOLS', 'Tools & Equipment'
        ELECTRONICS = 'ELECTRONICS', 'Electronics'
        OTHER = 'OTHER', 'Other'
    
    class Unit(models.TextChoices):
        PIECE = 'PIECE', 'Piece'
        BOX = 'BOX', 'Box'
        PACK = 'PACK', 'Pack'
        BOTTLE = 'BOTTLE', 'Bottle'
        CAN = 'CAN', 'Can'
        BAG = 'BAG', 'Bag'
        METER = 'METER', 'Meter'
        LITER = 'LITER', 'Liter'
        KILOGRAM = 'KILOGRAM', 'Kilogram'
    
    # Core fields
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices)
    unit = models.CharField(max_length=20, choices=Unit.choices)
    
    # Description and specifications
    description = models.TextField(blank=True, null=True)
    specifications = models.JSONField(default=dict, blank=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    
    # Storage and handling
    storage_conditions = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    min_stock_level = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'item'
        indexes = [
            models.Index(fields=['category', 'sku']),
            models.Index(fields=['name', 'brand']),
        ]
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.get_category_display()}"


class ShelterStock(models.Model):
    """Inventory stock levels at each shelter."""
    
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='shelter_stocks')
    
    # Stock levels
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reserved_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Location within shelter
    storage_location = models.CharField(max_length=100, blank=True, null=True)
    storage_notes = models.TextField(blank=True, null=True)
    
    # Stock management
    last_restocked = models.DateTimeField(blank=True, null=True)
    last_audit = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shelter_stock'
        unique_together = ['shelter', 'item']
        indexes = [
            models.Index(fields=['shelter', 'item']),
            models.Index(fields=['item', 'quantity']),
        ]
    
    def __str__(self):
        return f"{self.shelter.name} - {self.item.name}: {self.quantity} {self.item.unit}"
    
    @property
    def available_quantity(self):
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def is_low_stock(self):
        return self.available_quantity <= self.item.min_stock_level


class StockTransaction(models.Model):
    """Track all stock movements and transactions."""
    
    class TransactionType(models.TextChoices):
        IN = 'IN', 'Stock In'
        OUT = 'OUT', 'Stock Out'
        ADJUST = 'ADJUST', 'Stock Adjustment'
        RESERVE = 'RESERVE', 'Reserve Stock'
        RELEASE = 'RELEASE', 'Release Reserved Stock'
        TRANSFER = 'TRANSFER', 'Transfer Between Shelters'
        AUDIT = 'AUDIT', 'Stock Audit'
    
    class Reason(models.TextChoices):
        RESTOCK = 'RESTOCK', 'Restocking'
        DISTRIBUTION = 'DISTRIBUTION', 'Distribution to Beneficiaries'
        DAMAGED = 'DAMAGED', 'Damaged/Expired'
        THEFT = 'THEFT', 'Theft/Loss'
        AUDIT = 'AUDIT', 'Audit Correction'
        TRANSFER = 'TRANSFER', 'Transfer'
        OTHER = 'OTHER', 'Other'
    
    # Core fields
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shelter_stock = models.ForeignKey(ShelterStock, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    quantity = models.IntegerField()
    
    # Reference information
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # User tracking
    performed_by = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_transaction'
        indexes = [
            models.Index(fields=['shelter_stock', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
            models.Index(fields=['reason', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.quantity} {self.shelter_stock.item.unit} of {self.shelter_stock.item.name}"


class ShelterOccupancy(models.Model):
    """Track shelter occupancy over time."""
    
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE, related_name='occupancy_records')
    
    # Occupancy data
    occupancy_count = models.IntegerField(validators=[MinValueValidator(0)])
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional data
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'shelter_occupancy'
        indexes = [
            models.Index(fields=['shelter', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.shelter.name}: {self.occupancy_count} occupants at {self.timestamp}"


# Signal handlers for automatic updates
@receiver(post_save, sender=ShelterStock)
def create_stock_transaction(sender, instance, created, **kwargs):
    """Automatically create stock transaction when stock levels change."""
    if created:
        # New stock record
        StockTransaction.objects.create(
            shelter_stock=instance,
            transaction_type=StockTransaction.TransactionType.IN,
            reason=StockTransaction.Reason.RESTOCK,
            quantity=instance.quantity,
            notes="Initial stock"
        )


@receiver(post_save, sender=Shelter)
def create_occupancy_record(sender, instance, **kwargs):
    """Create occupancy record when shelter occupancy changes."""
    if 'current_occupancy' in kwargs.get('update_fields', []):
        ShelterOccupancy.objects.create(
            shelter=instance,
            occupancy_count=instance.current_occupancy
        )
