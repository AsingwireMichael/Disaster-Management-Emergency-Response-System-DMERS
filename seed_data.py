"""
Seed Data Script for DMERS
Populates the database with sample data for testing and demonstration
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.contrib.gis.geos import Point

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmers.settings')
django.setup()

from users.models import User, UserProfile
from incidents.models import Area, Incident, IncidentStatusHistory
from responders.models import ResponderUnit, ResponderAssignment, Dispatch
from logistics.models import Shelter, Item, ShelterStock
from analytics.models import DimDate, DimRegion, DimIncident, DimUnit


def create_sample_users():
    """Create sample users for different roles."""
    print("Creating sample users...")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        email='admin@dmers.org',
        defaults={
            'full_name': 'System Administrator',
            'phone': '+1234567890',
            'role': 'ADMIN',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Created admin user: {admin_user.email}")
    
    # Create command center user
    command_user, created = User.objects.get_or_create(
        email='command@dmers.org',
        defaults={
            'full_name': 'Command Center Operator',
            'phone': '+1234567891',
            'role': 'COMMAND'
        }
    )
    if created:
        command_user.set_password('command123')
        command_user.save()
        print(f"Created command user: {command_user.email}")
    
    # Create responder users
    responder_users = []
    responder_data = [
        ('medic1@dmers.org', 'John Smith', '+1234567892', 'RESPONDER'),
        ('medic2@dmers.org', 'Sarah Johnson', '+1234567893', 'RESPONDER'),
        ('fire1@dmers.org', 'Mike Wilson', '+1234567894', 'RESPONDER'),
        ('police1@dmers.org', 'Lisa Brown', '+1234567895', 'RESPONDER'),
    ]
    
    for email, name, phone, role in responder_data:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': name,
                'phone': phone,
                'role': role
            }
        )
        if created:
            user.set_password('responder123')
            user.save()
            print(f"Created responder user: {user.email}")
        responder_users.append(user)
    
    # Create citizen users
    citizen_users = []
    citizen_data = [
        ('citizen1@dmers.org', 'Alice Davis', '+1234567896'),
        ('citizen2@dmers.org', 'Bob Miller', '+1234567897'),
        ('citizen3@dmers.org', 'Carol Garcia', '+1234567898'),
    ]
    
    for email, name, phone in citizen_data:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': name,
                'phone': phone,
                'role': 'CITIZEN'
            }
        )
        if created:
            user.set_password('citizen123')
            user.save()
            print(f"Created citizen user: {user.email}")
        citizen_users.append(user)
    
    return admin_user, command_user, responder_users, citizen_users


def create_sample_areas():
    """Create sample geographic areas."""
    print("Creating sample areas...")
    
    areas = []
    area_data = [
        ('NORTH', 'North District', 'Northern part of the city'),
        ('SOUTH', 'South District', 'Southern part of the city'),
        ('EAST', 'East District', 'Eastern part of the city'),
        ('WEST', 'West District', 'Western part of the city'),
        ('CENTRAL', 'Central District', 'Central business district'),
    ]
    
    for code, name, description in area_data:
        area, created = Area.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'center': Point(-73.935242, 40.730610, srid=4326)  # NYC coordinates
            }
        )
        if created:
            print(f"Created area: {area.name}")
        areas.append(area)
    
    return areas


def create_sample_incidents(areas, users):
    """Create sample incidents."""
    print("Creating sample incidents...")
    
    admin_user, command_user, responder_users, citizen_users = users
    
    incidents = []
    incident_data = [
        # (category, severity, summary, description, area_code, reporter)
        ('FIRE', 4, 'Building fire in downtown', 'Large fire reported in office building', 'CENTRAL', citizen_users[0]),
        ('FLOOD', 3, 'River overflow in north district', 'River has burst its banks', 'NORTH', citizen_users[1]),
        ('ACCIDENT', 2, 'Car accident on highway', 'Multi-vehicle collision on I-95', 'SOUTH', citizen_users[2]),
        ('MEDICAL', 5, 'Heart attack emergency', 'Patient experiencing chest pain', 'EAST', citizen_users[0]),
        ('VIOLENCE', 3, 'Assault reported', 'Physical assault in parking lot', 'WEST', citizen_users[1]),
        ('NATURAL', 4, 'Tornado warning', 'Tornado spotted in area', 'CENTRAL', citizen_users[2]),
        ('FIRE', 2, 'Small kitchen fire', 'Minor fire in restaurant kitchen', 'SOUTH', citizen_users[0]),
        ('MEDICAL', 3, 'Broken leg', 'Patient with suspected broken leg', 'NORTH', citizen_users[1]),
    ]
    
    for category, severity, summary, description, area_code, reporter in incident_data:
        area = next(a for a in areas if a.code == area_code)
        
        incident = Incident.objects.create(
            reported_by=reporter,
            area=area,
            category=category,
            severity=severity,
            status='NEW',
            lat=40.730610 + (hash(area_code) % 100) / 10000,  # Slight variation
            lon=-73.935242 + (hash(area_code) % 100) / 10000,
            summary=summary,
            description=description,
            tags=[category.lower(), 'emergency']
        )
        
        print(f"Created incident: {incident.summary[:30]}...")
        incidents.append(incident)
    
    return incidents


def create_sample_responder_units():
    """Create sample responder units."""
    print("Creating sample responder units...")
    
    units = []
    unit_data = [
        ('AMB-001', 'AMBULANCE', 'North District', 2),
        ('AMB-002', 'AMBULANCE', 'South District', 2),
        ('FT-001', 'FIRE_TRUCK', 'Central District', 6),
        ('FT-002', 'FIRE_TRUCK', 'East District', 6),
        ('POL-001', 'POLICE', 'West District', 2),
        ('RESCUE-001', 'RESCUE', 'Central District', 4),
    ]
    
    for name, unit_type, home_area, capacity in unit_data:
        unit = ResponderUnit.objects.create(
            name=name,
            unit_type=unit_type,
            home_area=home_area,
            capacity=capacity,
            current_lat=40.730610,
            current_lon=-73.935242,
            capabilities=['emergency_response', 'medical_aid'],
            equipment=['radio', 'medical_supplies', 'defibrillator']
        )
        
        print(f"Created responder unit: {unit.name}")
        units.append(unit)
    
    return units


def create_sample_shelters(areas):
    """Create sample emergency shelters."""
    print("Creating sample shelters...")
    
    shelters = []
    shelter_data = [
        ('Emergency Shelter North', 'EMERGENCY', 'NORTH', 100, 0),
        ('Temporary Shelter South', 'TEMPORARY', 'SOUTH', 50, 0),
        ('Medical Shelter Central', 'MEDICAL', 'CENTRAL', 75, 0),
        ('Children Shelter East', 'CHILDREN', 'EAST', 30, 0),
        ('Animal Shelter West', 'ANIMAL', 'WEST', 25, 0),
    ]
    
    for name, shelter_type, area_code, capacity, occupancy in shelter_data:
        area = next(a for a in areas if a.code == area_code)
        
        shelter = Shelter.objects.create(
            name=name,
            shelter_type=shelter_type,
            area=area,
            address=f"123 {name} Street, {area.name}",
            lat=40.730610 + (hash(area_code) % 100) / 10000,
            lon=-73.935242 + (hash(area_code) % 100) / 10000,
            capacity=capacity,
            max_occupancy=capacity,
            current_occupancy=occupancy,
            facilities=['beds', 'showers', 'kitchen'],
            services=['medical', 'counseling', 'food'],
            open_24_7=True
        )
        
        print(f"Created shelter: {shelter.name}")
        shelters.append(shelter)
    
    return shelters


def create_sample_items():
    """Create sample inventory items."""
    print("Creating sample items...")
    
    items = []
    item_data = [
        ('FOOD-001', 'Food & Water', 'FOOD', 'PIECE', 'Emergency Food Rations', 100),
        ('MED-001', 'Medical Supplies', 'MEDICAL', 'BOX', 'First Aid Kit', 50),
        ('HYG-001', 'Hygiene Items', 'HYGIENE', 'PACK', 'Hygiene Kit', 75),
        ('CLOTH-001', 'Clothing & Bedding', 'CLOTHING', 'PIECE', 'Emergency Blanket', 200),
        ('TOOL-001', 'Tools & Equipment', 'TOOLS', 'PIECE', 'Flashlight', 100),
        ('MED-002', 'Medical Supplies', 'MEDICAL', 'BOTTLE', 'Pain Reliever', 150),
        ('FOOD-002', 'Food & Water', 'FOOD', 'BOTTLE', 'Water Bottles', 300),
    ]
    
    for sku, name, category, unit, description, min_stock in item_data:
        item = Item.objects.create(
            sku=sku,
            name=name,
            category=category,
            unit=unit,
            description=description,
            min_stock_level=min_stock
        )
        
        print(f"Created item: {item.name}")
        items.append(item)
    
    return items


def create_sample_shelter_stocks(shelters, items):
    """Create sample shelter stock levels."""
    print("Creating sample shelter stocks...")
    
    for shelter in shelters:
        for item in items:
            # Random stock levels
            import random
            quantity = random.randint(50, 200)
            reserved = random.randint(0, 20)
            
            stock = ShelterStock.objects.create(
                shelter=shelter,
                item=item,
                quantity=quantity,
                reserved_quantity=reserved,
                storage_location=f"Section {random.randint(1, 5)}",
                last_restocked=datetime.now() - timedelta(days=random.randint(1, 30))
            )
        
        print(f"Created stock records for shelter: {shelter.name}")


def create_sample_dispatches(incidents, units, users):
    """Create sample dispatch records."""
    print("Creating sample dispatches...")
    
    command_user = users[1]  # Command center user
    
    # Dispatch some incidents
    for i, incident in enumerate(incidents[:4]):  # Dispatch first 4 incidents
        unit = units[i % len(units)]
        
        # Update incident status
        incident.status = 'DISPATCHED'
        incident.dispatched_at = datetime.now() - timedelta(minutes=random.randint(5, 30))
        incident.save()
        
        # Create dispatch
        dispatch = Dispatch.objects.create(
            incident=incident,
            unit=unit,
            status='ON_SCENE',
            acknowledged_at=incident.dispatched_at + timedelta(minutes=2),
            en_route_at=incident.dispatched_at + timedelta(minutes=5),
            arrived_at=incident.dispatched_at + timedelta(minutes=15),
            outcome='SUCCESS'
        )
        
        print(f"Created dispatch: {unit.name} → {incident.summary[:30]}...")


def create_sample_analytics_data(areas, incidents, units):
    """Create sample analytics data."""
    print("Creating sample analytics data...")
    
    # Create date dimension for last 30 days
    today = datetime.now().date()
    for i in range(30):
        date = today - timedelta(days=i)
        
        date_dim, created = DimDate.objects.get_or_create(
            date_key=date,
            defaults={
                'year': date.year,
                'quarter': (date.month - 1) // 3 + 1,
                'month': date.month,
                'month_name': date.strftime('%B'),
                'week_of_year': date.isocalendar()[1],
                'day_of_year': date.timetuple().tm_yday,
                'day_of_month': date.day,
                'day_of_week': date.weekday(),
                'day_name': date.strftime('%A'),
                'is_weekend': date.weekday() >= 5,
                'is_holiday': False
            }
        )
    
    # Create region dimensions
    for area in areas:
        region_dim, created = DimRegion.objects.get_or_create(
            area_code=area.code,
            defaults={
                'area_name': area.name,
                'region_type': 'OPERATIONAL',
                'center_lat': area.center.y if area.center else 40.730610,
                'center_lon': area.center.x if area.center else -73.935242
            }
        )
    
    # Create incident dimensions
    for incident in incidents:
        incident_dim, created = DimIncident.objects.get_or_create(
            incident_id=str(incident.incident_id),
            defaults={
                'category': incident.category,
                'severity': incident.severity,
                'status': incident.status,
                'priority_score': incident.priority_score,
                'lat': incident.lat,
                'lon': incident.lon,
                'reporter_role': incident.reported_by.role,
                'reporter_area': incident.area.code,
                'created_date_key': DimDate.objects.get(date_key=incident.created_at.date())
            }
        )
    
    # Create unit dimensions
    for unit in units:
        unit_dim, created = DimUnit.objects.get_or_create(
            unit_id=str(unit.unit_id),
            defaults={
                'unit_name': unit.name,
                'unit_type': unit.unit_type,
                'home_area': unit.home_area,
                'capacity': unit.capacity
            }
        )
    
    print("Created analytics dimension tables")


def main():
    """Main function to create all sample data."""
    print("Starting DMERS seed data creation...")
    
    try:
        # Create users
        users = create_sample_users()
        
        # Create areas
        areas = create_sample_areas()
        
        # Create incidents
        incidents = create_sample_incidents(areas, users)
        
        # Create responder units
        units = create_sample_responder_units()
        
        # Create shelters
        shelters = create_sample_shelters(areas)
        
        # Create items
        items = create_sample_items()
        
        # Create shelter stocks
        create_sample_shelter_stocks(shelters, items)
        
        # Create dispatches
        create_sample_dispatches(incidents, units, users)
        
        # Create analytics data
        create_sample_analytics_data(areas, incidents, units)
        
        print("\n✅ Seed data creation completed successfully!")
        print(f"Created:")
        print(f"  - {len(users[0:3])} system users")
        print(f"  - {len(areas)} geographic areas")
        print(f"  - {len(incidents)} incidents")
        print(f"  - {len(units)} responder units")
        print(f"  - {len(shelters)} shelters")
        print(f"  - {len(items)} inventory items")
        
        print("\n🔑 Default login credentials:")
        print("  Admin: admin@dmers.org / admin123")
        print("  Command: command@dmers.org / command123")
        print("  Responder: medic1@dmers.org / responder123")
        print("  Citizen: citizen1@dmers.org / citizen123")
        
    except Exception as e:
        print(f"❌ Error creating seed data: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
