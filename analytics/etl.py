"""
ETL Script for DMERS Data Warehouse
Populates dimension and fact tables from operational databases
"""

import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Count, Avg, Min, Max, Sum, Q
from django.contrib.gis.geos import Point
from django.utils import timezone
from incidents.models import Incident, Area, IncidentStatusHistory
from responders.models import ResponderUnit, Dispatch, SituationReport
from logistics.models import Shelter, ShelterStock, Item
from users.models import User
from .models import (
    DimDate, DimRegion, DimIncident, DimUnit,
    FactIncidentDaily, FactResponse, FactShelterUtilization, FactInventory
)

logger = logging.getLogger(__name__)


class DMERSEtlProcessor:
    """Main ETL processor for DMERS data warehouse."""
    
    def __init__(self):
        self.processed_dates = set()
        self.processed_regions = set()
        self.processed_incidents = set()
        self.processed_units = set()
    
    def run_full_etl(self, start_date=None, end_date=None):
        """Run full ETL process for specified date range."""
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        logger.info(f"Starting full ETL process from {start_date} to {end_date}")
        
        try:
            with transaction.atomic():
                # Process dimensions first
                self.process_dimensions(start_date, end_date)
                
                # Process facts
                self.process_facts(start_date, end_date)
                
                # Update aggregations
                self.update_aggregations(start_date, end_date)
                
            logger.info("Full ETL process completed successfully")
            
        except Exception as e:
            logger.error(f"ETL process failed: {str(e)}")
            raise
    
    def process_dimensions(self, start_date, end_date):
        """Process and populate dimension tables."""
        logger.info("Processing dimension tables...")
        
        # Process date dimension
        self.process_dim_date(start_date, end_date)
        
        # Process region dimension
        self.process_dim_region()
        
        # Process incident dimension
        self.process_dim_incident(start_date, end_date)
        
        # Process unit dimension
        self.process_dim_unit()
        
        logger.info("Dimension tables processed successfully")
    
    def process_dim_date(self, start_date, end_date):
        """Populate date dimension table."""
        current_date = start_date
        while current_date <= end_date:
            if current_date not in self.processed_dates:
                date_obj, created = DimDate.objects.get_or_create(
                    date_key=current_date,
                    defaults={
                        'year': current_date.year,
                        'quarter': (current_date.month - 1) // 3 + 1,
                        'month': current_date.month,
                        'month_name': current_date.strftime('%B'),
                        'week_of_year': current_date.isocalendar()[1],
                        'day_of_year': current_date.timetuple().tm_yday,
                        'day_of_month': current_date.day,
                        'day_of_week': current_date.weekday(),
                        'day_name': current_date.strftime('%A'),
                        'is_weekend': current_date.weekday() >= 5,
                        'is_holiday': False  # Could be enhanced with holiday calendar
                    }
                )
                if created:
                    logger.debug(f"Created date dimension for {current_date}")
                self.processed_dates.add(current_date)
            
            current_date += timedelta(days=1)
    
    def process_dim_region(self):
        """Populate region dimension table."""
        areas = Area.objects.all()
        
        for area in areas:
            if area.code not in self.processed_regions:
                region_obj, created = DimRegion.objects.get_or_create(
                    area_code=area.code,
                    defaults={
                        'area_name': area.name,
                        'region_type': 'OPERATIONAL',
                        'center_lat': area.center.y if area.center else None,
                        'center_lon': area.center.x if area.center else None,
                        'center_location': area.center
                    }
                )
                if created:
                    logger.debug(f"Created region dimension for {area.code}")
                self.processed_regions.add(area.code)
    
    def process_dim_incident(self, start_date, end_date):
        """Populate incident dimension table."""
        incidents = Incident.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('reported_by', 'area')
        
        for incident in incidents:
            if str(incident.incident_id) not in self.processed_incidents:
                # Get or create date dimensions
                created_date = DimDate.objects.get(date_key=incident.created_at.date())
                resolved_date = None
                if incident.resolved_at:
                    resolved_date = DimDate.objects.get(date_key=incident.resolved_at.date())
                
                incident_dim, created = DimIncident.objects.get_or_create(
                    incident_id=str(incident.incident_id),
                    defaults={
                        'category': incident.category,
                        'severity': incident.severity,
                        'status': incident.status,
                        'priority_score': incident.priority_score,
                        'lat': incident.lat,
                        'lon': incident.lon,
                        'location': incident.location,
                        'created_date_key': created_date,
                        'resolved_date_key': resolved_date,
                        'reporter_role': incident.reported_by.role,
                        'reporter_area': incident.area.code
                    }
                )
                if created:
                    logger.debug(f"Created incident dimension for {incident.incident_id}")
                self.processed_incidents.add(str(incident.incident_id))
    
    def process_dim_unit(self):
        """Populate unit dimension table."""
        units = ResponderUnit.objects.all()
        
        for unit in units:
            if str(unit.unit_id) not in self.processed_units:
                unit_dim, created = DimUnit.objects.get_or_create(
                    unit_id=str(unit.unit_id),
                    defaults={
                        'unit_name': unit.name,
                        'unit_type': unit.unit_type,
                        'home_area': unit.home_area,
                        'capacity': unit.capacity
                    }
                )
                if created:
                    logger.debug(f"Created unit dimension for {unit.unit_id}")
                self.processed_units.add(str(unit.unit_id))
    
    def process_facts(self, start_date, end_date):
        """Process and populate fact tables."""
        logger.info("Processing fact tables...")
        
        # Process daily incident facts
        self.process_fact_incident_daily(start_date, end_date)
        
        # Process response facts
        self.process_fact_response(start_date, end_date)
        
        # Process shelter utilization facts
        self.process_fact_shelter_utilization(start_date, end_date)
        
        # Process inventory facts
        self.process_fact_inventory(start_date, end_date)
        
        logger.info("Fact tables processed successfully")
    
    def process_fact_incident_daily(self, start_date, end_date):
        """Populate daily incident facts."""
        current_date = start_date
        while current_date <= end_date:
            # Get all regions
            regions = DimRegion.objects.all()
            
            for region in regions:
                # Get incidents for this date and region
                incidents = Incident.objects.filter(
                    created_at__date=current_date,
                    area__code=region.area_code
                )
                
                if incidents.exists():
                    # Calculate metrics
                    total_incidents = incidents.count()
                    new_incidents = incidents.filter(status='NEW').count()
                    resolved_incidents = incidents.filter(status='RESOLVED').count()
                    closed_incidents = incidents.filter(status='CLOSED').count()
                    
                    avg_severity = incidents.aggregate(avg_sev=Avg('severity'))['avg_sev'] or 0
                    max_severity = incidents.aggregate(max_sev=Max('severity'))['max_sev'] or 0
                    min_severity = incidents.aggregate(min_sev=Min('severity'))['min_sev'] or 0
                    
                    # Category breakdown
                    fire_incidents = incidents.filter(category='FIRE').count()
                    flood_incidents = incidents.filter(category='FLOOD').count()
                    accident_incidents = incidents.filter(category='ACCIDENT').count()
                    violence_incidents = incidents.filter(category='VIOLENCE').count()
                    medical_incidents = incidents.filter(category='MEDICAL').count()
                    natural_incidents = incidents.filter(category='NATURAL').count()
                    other_incidents = incidents.filter(category='OTHER').count()
                    
                    # Response time metrics
                    dispatched_incidents = incidents.filter(
                        status__in=['DISPATCHED', 'ONGOING', 'RESOLVED', 'CLOSED'],
                        dispatched_at__isnull=False
                    )
                    
                    avg_response_time = 0
                    total_response_time = 0
                    if dispatched_incidents.exists():
                        response_times = []
                        for incident in dispatched_incidents:
                            if incident.dispatched_at and incident.created_at:
                                response_time = (incident.dispatched_at - incident.created_at).total_seconds() / 60
                                response_times.append(response_time)
                        
                        if response_times:
                            avg_response_time = sum(response_times) / len(response_times)
                            total_response_time = sum(response_times)
                    
                    # Create or update fact record
                    date_dim = DimDate.objects.get(date_key=current_date)
                    
                    fact, created = FactIncidentDaily.objects.get_or_create(
                        date_key=date_dim,
                        region_key=region,
                        defaults={
                            'total_incidents': total_incidents,
                            'new_incidents': new_incidents,
                            'resolved_incidents': resolved_incidents,
                            'closed_incidents': closed_incidents,
                            'avg_severity': avg_severity,
                            'max_severity': max_severity,
                            'min_severity': min_severity,
                            'fire_incidents': fire_incidents,
                            'flood_incidents': flood_incidents,
                            'accident_incidents': accident_incidents,
                            'violence_incidents': violence_incidents,
                            'medical_incidents': medical_incidents,
                            'natural_incidents': natural_incidents,
                            'other_incidents': other_incidents,
                            'avg_response_time_minutes': avg_response_time,
                            'total_response_time_minutes': total_response_time
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        fact.total_incidents = total_incidents
                        fact.new_incidents = new_incidents
                        fact.resolved_incidents = resolved_incidents
                        fact.closed_incidents = closed_incidents
                        fact.avg_severity = avg_severity
                        fact.max_severity = max_severity
                        fact.min_severity = min_severity
                        fact.fire_incidents = fire_incidents
                        fact.flood_incidents = flood_incidents
                        fact.accident_incidents = accident_incidents
                        fact.violence_incidents = violence_incidents
                        fact.medical_incidents = medical_incidents
                        fact.natural_incidents = natural_incidents
                        fact.other_incidents = other_incidents
                        fact.avg_response_time_minutes = avg_response_time
                        fact.total_response_time_minutes = total_response_time
                        fact.save()
            
            current_date += timedelta(days=1)
    
    def process_fact_response(self, start_date, end_date):
        """Populate response facts."""
        dispatches = Dispatch.objects.filter(
            assigned_at__date__gte=start_date,
            assigned_at__date__lte=end_date
        ).select_related('incident', 'unit', 'incident__area')
        
        for dispatch in dispatches:
            # Get dimension keys
            try:
                date_dim = DimDate.objects.get(date_key=dispatch.assigned_at.date())
                incident_dim = DimIncident.objects.get(incident_id=str(dispatch.incident.incident_id))
                unit_dim = DimUnit.objects.get(unit_id=str(dispatch.unit.unit_id))
                region_dim = DimRegion.objects.get(area_code=dispatch.incident.area.code)
                
                # Calculate timing metrics
                dispatch_time = 0
                response_time = 0
                on_scene_time = 0
                total_response_time = 0
                
                if dispatch.assigned_at and dispatch.incident.created_at:
                    dispatch_time = (dispatch.assigned_at - dispatch.incident.created_at).total_seconds() / 60
                
                if dispatch.arrived_at and dispatch.assigned_at:
                    response_time = (dispatch.arrived_at - dispatch.assigned_at).total_seconds() / 60
                
                if dispatch.cleared_at and dispatch.arrived_at:
                    on_scene_time = (dispatch.cleared_at - dispatch.arrived_at).total_seconds() / 60
                
                if dispatch.cleared_at and dispatch.incident.created_at:
                    total_response_time = (dispatch.cleared_at - dispatch.incident.created_at).total_seconds() / 60
                
                # Create or update fact record
                fact, created = FactResponse.objects.get_or_create(
                    incident_key=incident_dim,
                    unit_key=unit_dim,
                    defaults={
                        'date_key': date_dim,
                        'region_key': region_dim,
                        'dispatch_time_minutes': dispatch_time,
                        'response_time_minutes': response_time,
                        'on_scene_time_minutes': on_scene_time,
                        'total_response_time_minutes': total_response_time,
                        'outcome': dispatch.outcome,
                        'casualties': 0,  # Would need to be extracted from situation reports
                        'fatalities': 0,   # Would need to be extracted from situation reports
                        'unit_distance_km': 0,  # Would need GPS tracking data
                        'unit_utilization_hours': 0  # Would need time tracking
                    }
                )
                
                if not created:
                    # Update existing record
                    fact.dispatch_time_minutes = dispatch_time
                    fact.response_time_minutes = response_time
                    fact.on_scene_time_minutes = on_scene_time
                    fact.total_response_time_minutes = total_response_time
                    fact.outcome = dispatch.outcome
                    fact.save()
                    
            except (DimDate.DoesNotExist, DimIncident.DoesNotExist, 
                   DimUnit.DoesNotExist, DimRegion.DoesNotExist):
                logger.warning(f"Missing dimension for dispatch {dispatch.dispatch_id}")
                continue
    
    def process_fact_shelter_utilization(self, start_date, end_date):
        """Populate shelter utilization facts."""
        current_date = start_date
        while current_date <= end_date:
            # Get all regions
            regions = DimRegion.objects.all()
            
            for region in regions:
                # Get shelters for this region
                shelters = Shelter.objects.filter(area__code=region.area_code)
                
                if shelters.exists():
                    total_shelters = shelters.count()
                    active_shelters = shelters.filter(status='ACTIVE').count()
                    total_capacity = sum(shelter.max_occupancy for shelter in shelters)
                    total_occupancy = sum(shelter.current_occupancy for shelter in shelters)
                    avg_occupancy_rate = (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0
                    
                    # Shelter type breakdown
                    emergency_shelters = shelters.filter(shelter_type='EMERGENCY').count()
                    temporary_shelters = shelters.filter(shelter_type='TEMPORARY').count()
                    medical_shelters = shelters.filter(shelter_type='MEDICAL').count()
                    
                    # Create or update fact record
                    date_dim = DimDate.objects.get(date_key=current_date)
                    
                    fact, created = FactShelterUtilization.objects.get_or_create(
                        date_key=date_dim,
                        region_key=region,
                        defaults={
                            'total_shelters': total_shelters,
                            'active_shelters': active_shelters,
                            'total_capacity': total_capacity,
                            'total_occupancy': total_occupancy,
                            'avg_occupancy_rate': avg_occupancy_rate,
                            'emergency_shelters': emergency_shelters,
                            'temporary_shelters': temporary_shelters,
                            'medical_shelters': medical_shelters
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        fact.total_shelters = total_shelters
                        fact.active_shelters = active_shelters
                        fact.total_capacity = total_capacity
                        fact.total_occupancy = total_occupancy
                        fact.avg_occupancy_rate = avg_occupancy_rate
                        fact.emergency_shelters = emergency_shelters
                        fact.temporary_shelters = temporary_shelters
                        fact.medical_shelters = medical_shelters
                        fact.save()
            
            current_date += timedelta(days=1)
    
    def process_fact_inventory(self, start_date, end_date):
        """Populate inventory facts."""
        current_date = start_date
        while current_date <= end_date:
            # Get all regions
            regions = DimRegion.objects.all()
            
            for region in regions:
                # Get inventory for this region
                shelter_stocks = ShelterStock.objects.filter(
                    shelter__area__code=region.area_code
                ).select_related('item')
                
                if shelter_stocks.exists():
                    total_items = sum(stock.quantity for stock in shelter_stocks)
                    low_stock_items = sum(1 for stock in shelter_stocks if stock.is_low_stock)
                    out_of_stock_items = sum(1 for stock in shelter_stocks if stock.quantity == 0)
                    
                    # Category breakdown
                    food_water_items = sum(
                        stock.quantity for stock in shelter_stocks 
                        if stock.item.category == 'FOOD'
                    )
                    medical_items = sum(
                        stock.quantity for stock in shelter_stocks 
                        if stock.item.category == 'MEDICAL'
                    )
                    hygiene_items = sum(
                        stock.quantity for stock in shelter_stocks 
                        if stock.item.category == 'HYGIENE'
                    )
                    clothing_items = sum(
                        stock.quantity for stock in shelter_stocks 
                        if stock.item.category == 'CLOTHING'
                    )
                    tool_items = sum(
                        stock.quantity for stock in shelter_stocks 
                        if stock.item.category == 'TOOLS'
                    )
                    
                    # Create or update fact record
                    date_dim = DimDate.objects.get(date_key=current_date)
                    
                    fact, created = FactInventory.objects.get_or_create(
                        date_key=date_dim,
                        region_key=region,
                        defaults={
                            'total_items': total_items,
                            'low_stock_items': low_stock_items,
                            'out_of_stock_items': out_of_stock_items,
                            'food_water_items': food_water_items,
                            'medical_items': medical_items,
                            'hygiene_items': hygiene_items,
                            'clothing_items': clothing_items,
                            'tool_items': tool_items,
                            'items_distributed': 0,  # Would need transaction history
                            'items_restocked': 0,    # Would need transaction history
                            'items_expired': 0       # Would need expiry tracking
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        fact.total_items = total_items
                        fact.low_stock_items = low_stock_items
                        fact.out_of_stock_items = out_of_stock_items
                        fact.food_water_items = food_water_items
                        fact.medical_items = medical_items
                        fact.hygiene_items = hygiene_items
                        fact.clothing_items = clothing_items
                        fact.tool_items = tool_items
                        fact.save()
            
            current_date += timedelta(days=1)
    
    def update_aggregations(self, start_date, end_date):
        """Update aggregated metrics and summary tables."""
        logger.info("Updating aggregations...")
        
        # This method would update summary tables, materialized views, or other aggregations
        # For now, it's a placeholder for future enhancements
        
        logger.info("Aggregations updated successfully")


def run_etl_job(start_date=None, end_date=None):
    """Convenience function to run ETL job."""
    processor = DMERSEtlProcessor()
    processor.run_full_etl(start_date, end_date)


def run_daily_etl():
    """Run daily ETL job for current day."""
    today = timezone.now().date()
    processor = DMERSEtlProcessor()
    processor.run_full_etl(today, today)


def run_weekly_etl():
    """Run weekly ETL job for current week."""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    processor = DMERSEtlProcessor()
    processor.run_full_etl(week_start, week_end)


def run_monthly_etl():
    """Run monthly ETL job for current month."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    processor = DMERSEtlProcessor()
    processor.run_full_etl(month_start, month_end)
