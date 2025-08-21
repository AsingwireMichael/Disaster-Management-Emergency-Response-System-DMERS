from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    DimDate, DimRegion, DimIncident, DimUnit,
    FactIncidentDaily, FactResponse, FactShelterUtilization, FactInventory
)
from .etl import run_etl_job, run_daily_etl, run_weekly_etl, run_monthly_etl


class AnalyticsBaseView(generics.GenericAPIView):
    """Base view for analytics with common functionality."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_date_range(self, request):
        """Get date range from request parameters."""
        end_date = timezone.now().date()
        
        # Default to last 30 days
        days = int(request.query_params.get('days', 30))
        start_date = end_date - timedelta(days=days)
        
        # Override with specific dates if provided
        if 'start_date' in request.query_params:
            start_date = timezone.datetime.strptime(
                request.query_params['start_date'], '%Y-%m-%d'
            ).date()
        
        if 'end_date' in request.query_params:
            end_date = timezone.datetime.strptime(
                request.query_params['end_date'], '%Y-%m-%d'
            ).date()
        
        return start_date, end_date


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_trends(request):
    """Get incident trends over time."""
    try:
        # Get date range
        end_date = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        start_date = end_date - timedelta(days=days)
        
        # Get daily incident facts
        daily_facts = FactIncidentDaily.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('region_key').order_by('date_key')
        
        # Aggregate by date
        trends = {}
        for fact in daily_facts:
            date_str = fact.date_key.date().isoformat()
            if date_str not in trends:
                trends[date_str] = {
                    'date': date_str,
                    'total_incidents': 0,
                    'new_incidents': 0,
                    'resolved_incidents': 0,
                    'avg_severity': 0,
                    'avg_response_time': 0,
                    'regions': {}
                }
            
            trends[date_str]['total_incidents'] += fact.total_incidents
            trends[date_str]['new_incidents'] += fact.new_incidents
            trends[date_str]['resolved_incidents'] += fact.resolved_incidents
            
            # Weighted average for severity and response time
            if fact.total_incidents > 0:
                trends[date_str]['avg_severity'] += fact.avg_severity * fact.total_incidents
                trends[date_str]['avg_response_time'] += fact.avg_response_time_minutes * fact.total_incidents
            
            # Regional breakdown
            region_name = fact.region_key.area_name
            if region_name not in trends[date_str]['regions']:
                trends[date_str]['regions'][region_name] = {
                    'incidents': fact.total_incidents,
                    'avg_severity': fact.avg_severity
                }
        
        # Calculate final averages
        for date_data in trends.values():
            total_incidents = date_data['total_incidents']
            if total_incidents > 0:
                date_data['avg_severity'] = round(date_data['avg_severity'] / total_incidents, 2)
                date_data['avg_response_time'] = round(date_data['avg_response_time'] / total_incidents, 2)
        
        return Response({
            'trends': list(trends.values()),
            'summary': {
                'total_days': len(trends),
                'total_incidents': sum(t['total_incidents'] for t in trends.values()),
                'avg_daily_incidents': round(
                    sum(t['total_incidents'] for t in trends.values()) / len(trends), 2
                ) if trends else 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve incident trends: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def regional_analysis(request):
    """Get regional analysis of incidents and response."""
    try:
        # Get date range
        end_date = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        start_date = end_date - timedelta(days=days)
        
        # Get regional facts
        regional_facts = FactIncidentDaily.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('region_key').values('region_key__area_name').annotate(
            total_incidents=Sum('total_incidents'),
            avg_severity=Avg('avg_severity'),
            avg_response_time=Avg('avg_response_time_minutes'),
            fire_incidents=Sum('fire_incidents'),
            flood_incidents=Sum('flood_incidents'),
            accident_incidents=Sum('accident_incidents'),
            medical_incidents=Sum('medical_incidents')
        ).order_by('-total_incidents')
        
        # Get shelter utilization
        shelter_facts = FactShelterUtilization.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('region_key').values('region_key__area_name').annotate(
            avg_occupancy_rate=Avg('avg_occupancy_rate'),
            total_capacity=Sum('total_capacity'),
            total_shelters=Sum('total_shelters')
        )
        
        # Combine data
        regional_data = {}
        for fact in regional_facts:
            region_name = fact['region_key__area_name']
            regional_data[region_name] = {
                'region': region_name,
                'incidents': {
                    'total': fact['total_incidents'] or 0,
                    'avg_severity': round(fact['avg_severity'] or 0, 2),
                    'avg_response_time': round(fact['avg_response_time'] or 0, 2),
                    'by_category': {
                        'fire': fact['fire_incidents'] or 0,
                        'flood': fact['flood_incidents'] or 0,
                        'accident': fact['accident_incidents'] or 0,
                        'medical': fact['medical_incidents'] or 0
                    }
                },
                'shelters': {
                    'total': 0,
                    'capacity': 0,
                    'avg_occupancy_rate': 0
                }
            }
        
        # Add shelter data
        for shelter_fact in shelter_facts:
            region_name = shelter_fact['region_key__area_name']
            if region_name in regional_data:
                regional_data[region_name]['shelters'] = {
                    'total': shelter_fact['total_shelters'] or 0,
                    'capacity': shelter_fact['total_capacity'] or 0,
                    'avg_occupancy_rate': round(shelter_fact['avg_occupancy_rate'] or 0, 2)
                }
        
        return Response({
            'regional_analysis': list(regional_data.values()),
            'summary': {
                'total_regions': len(regional_data),
                'total_incidents': sum(r['incidents']['total'] for r in regional_data.values()),
                'avg_regional_incidents': round(
                    sum(r['incidents']['total'] for r in regional_data.values()) / len(regional_data), 2
                ) if regional_data else 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve regional analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def response_performance(request):
    """Get response unit performance metrics."""
    try:
        # Get date range
        end_date = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        start_date = end_date - timedelta(days=days)
        
        # Get response facts
        response_facts = FactResponse.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('unit_key', 'region_key').values(
            'unit_key__unit_name', 'unit_key__unit_type', 'unit_key__home_area'
        ).annotate(
            total_dispatches=Count('fact_key'),
            avg_response_time=Avg('response_time_minutes'),
            avg_dispatch_time=Avg('dispatch_time_minutes'),
            avg_on_scene_time=Avg('on_scene_time_minutes'),
            success_rate=Count('fact_key', filter=Q(outcome='SUCCESS')) * 100.0 / Count('fact_key')
        ).order_by('-total_dispatches')
        
        # Get unit utilization
        unit_facts = FactResponse.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('unit_key').values('unit_key__unit_name').annotate(
            total_utilization_hours=Sum('unit_utilization_hours'),
            avg_distance=Avg('unit_distance_km')
        )
        
        # Combine data
        unit_performance = {}
        for fact in response_facts:
            unit_name = fact['unit_key__unit_name']
            unit_performance[unit_name] = {
                'unit_name': unit_name,
                'unit_type': fact['unit_key__unit_type'],
                'home_area': fact['unit_key__home_area'],
                'performance': {
                    'total_dispatches': fact['total_dispatches'],
                    'avg_response_time': round(fact['avg_response_time'] or 0, 2),
                    'avg_dispatch_time': round(fact['avg_dispatch_time'] or 0, 2),
                    'avg_on_scene_time': round(fact['avg_on_scene_time'] or 0, 2),
                    'success_rate': round(fact['success_rate'] or 0, 2)
                },
                'utilization': {
                    'total_hours': 0,
                    'avg_distance': 0
                }
            }
        
        # Add utilization data
        for util_fact in unit_facts:
            unit_name = util_fact['unit_key__unit_name']
            if unit_name in unit_performance:
                unit_performance[unit_name]['utilization'] = {
                    'total_hours': round(util_fact['total_utilization_hours'] or 0, 2),
                    'avg_distance': round(util_fact['avg_distance'] or 0, 2)
                }
        
        return Response({
            'unit_performance': list(unit_performance.values()),
            'summary': {
                'total_units': len(unit_performance),
                'total_dispatches': sum(u['performance']['total_dispatches'] for u in unit_performance.values()),
                'avg_response_time': round(
                    sum(u['performance']['avg_response_time'] for u in unit_performance.values()) / len(unit_performance), 2
                ) if unit_performance else 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve response performance: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def inventory_analysis(request):
    """Get inventory and supply chain analysis."""
    try:
        # Get date range
        end_date = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        start_date = end_date - timedelta(days=days)
        
        # Get inventory facts
        inventory_facts = FactInventory.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('region_key').values('region_key__area_name').annotate(
            avg_total_items=Avg('total_items'),
            avg_low_stock=Avg('low_stock_items'),
            avg_out_of_stock=Avg('out_of_stock_items'),
            avg_food_water=Avg('food_water_items'),
            avg_medical=Avg('medical_items'),
            avg_hygiene=Avg('hygiene_items'),
            avg_clothing=Avg('clothing_items'),
            avg_tools=Avg('tool_items')
        ).order_by('region_key__area_name')
        
        # Get shelter utilization for context
        shelter_facts = FactShelterUtilization.objects.filter(
            date_key__date__gte=start_date,
            date_key__date__lte=end_date
        ).select_related('region_key').values('region_key__area_name').annotate(
            avg_occupancy=Avg('avg_occupancy_rate'),
            avg_capacity=Avg('total_capacity')
        )
        
        # Combine data
        inventory_data = {}
        for fact in inventory_facts:
            region_name = fact['region_key__area_name']
            inventory_data[region_name] = {
                'region': region_name,
                'inventory': {
                    'total_items': round(fact['avg_total_items'] or 0, 2),
                    'low_stock_items': round(fact['avg_low_stock'] or 0, 2),
                    'out_of_stock_items': round(fact['avg_out_of_stock'] or 0, 2),
                    'by_category': {
                        'food_water': round(fact['avg_food_water'] or 0, 2),
                        'medical': round(fact['avg_medical'] or 0, 2),
                        'hygiene': round(fact['avg_hygiene'] or 0, 2),
                        'clothing': round(fact['avg_clothing'] or 0, 2),
                        'tools': round(fact['avg_tools'] or 0, 2)
                    }
                },
                'shelter_context': {
                    'avg_occupancy_rate': 0,
                    'avg_capacity': 0
                }
            }
        
        # Add shelter context
        for shelter_fact in shelter_facts:
            region_name = shelter_fact['region_key__area_name']
            if region_name in inventory_data:
                inventory_data[region_name]['shelter_context'] = {
                    'avg_occupancy_rate': round(shelter_fact['avg_occupancy'] or 0, 2),
                    'avg_capacity': round(shelter_fact['avg_capacity'] or 0, 2)
                }
        
        return Response({
            'inventory_analysis': list(inventory_data.values()),
            'summary': {
                'total_regions': len(inventory_data),
                'total_items': sum(r['inventory']['total_items'] for r in inventory_data.values()),
                'avg_low_stock_rate': round(
                    sum(r['inventory']['low_stock_items'] for r in inventory_data.values()) / 
                    sum(r['inventory']['total_items'] for r in inventory_data.values()) * 100, 2
                ) if sum(r['inventory']['total_items'] for r in inventory_data.values()) > 0 else 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve inventory analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def trigger_etl(request):
    """Trigger ETL process manually (admin only)."""
    try:
        etl_type = request.data.get('type', 'daily')
        
        if etl_type == 'daily':
            run_daily_etl()
            message = "Daily ETL process completed"
        elif etl_type == 'weekly':
            run_weekly_etl()
            message = "Weekly ETL process completed"
        elif etl_type == 'monthly':
            run_monthly_etl()
            message = "Monthly ETL process completed"
        elif etl_type == 'custom':
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            if start_date and end_date:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                run_etl_job(start_date, end_date)
                message = f"Custom ETL process completed for {start_date} to {end_date}"
            else:
                return Response(
                    {'error': 'start_date and end_date required for custom ETL'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Invalid ETL type. Use: daily, weekly, monthly, or custom'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'etl_type': etl_type,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'ETL process failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    """Get summary metrics for dashboard."""
    try:
        # Get current date
        today = timezone.now().date()
        
        # Get today's facts
        today_facts = FactIncidentDaily.objects.filter(date_key=today)
        
        # Get recent trends (last 7 days)
        week_ago = today - timedelta(days=7)
        weekly_facts = FactIncidentDaily.objects.filter(
            date_key__date__gte=week_ago,
            date_key__date__lte=today
        )
        
        # Calculate summary metrics
        today_total = today_facts.aggregate(total=Sum('total_incidents'))['total'] or 0
        today_active = today_facts.aggregate(active=Sum('new_incidents'))['active'] or 0
        
        weekly_total = weekly_facts.aggregate(total=Sum('total_incidents'))['total'] or 0
        weekly_avg = weekly_total / 7 if weekly_total > 0 else 0
        
        # Get regional breakdown
        regional_breakdown = today_facts.values('region_key__area_name').annotate(
            incidents=Sum('total_incidents')
        ).order_by('-incidents')[:5]
        
        # Get category breakdown
        category_breakdown = today_facts.aggregate(
            fire=Sum('fire_incidents'),
            flood=Sum('flood_incidents'),
            accident=Sum('accident_incidents'),
            medical=Sum('medical_incidents'),
            other=Sum('other_incidents')
        )
        
        return Response({
            'today': {
                'total_incidents': today_total,
                'active_incidents': today_active,
                'resolved_incidents': today_total - today_active
            },
            'weekly': {
                'total_incidents': weekly_total,
                'daily_average': round(weekly_avg, 2)
            },
            'regional_breakdown': list(regional_breakdown),
            'category_breakdown': {
                'fire': category_breakdown['fire'] or 0,
                'flood': category_breakdown['flood'] or 0,
                'accident': category_breakdown['accident'] or 0,
                'medical': category_breakdown['medical'] or 0,
                'other': category_breakdown['other'] or 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve dashboard summary: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
