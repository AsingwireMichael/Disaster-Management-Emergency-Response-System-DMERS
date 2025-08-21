from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Area, Incident, IncidentStatusHistory, IncidentMedia, IncidentNote
from .serializers import (
    AreaSerializer, IncidentSerializer, IncidentCreateSerializer, IncidentUpdateSerializer,
    IncidentListSerializer, IncidentMediaSerializer, IncidentNoteSerializer,
    IncidentMediaCreateSerializer, IncidentNoteCreateSerializer
)


class AreaListView(generics.ListAPIView):
    """List all geographic areas."""
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]


class IncidentListView(generics.ListCreateAPIView):
    """List and create incidents."""
    serializer_class = IncidentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'severity', 'status', 'area']
    search_fields = ['summary', 'description', 'address']
    ordering_fields = ['created_at', 'severity', 'priority_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Citizens can only see their own incidents
        if user.role == 'CITIZEN':
            return Incident.objects.filter(reported_by=user)
        
        # Responders and command can see all incidents
        return Incident.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IncidentCreateSerializer
        return IncidentListSerializer


class IncidentDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update incident details."""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'incident_id'
    
    def get_queryset(self):
        user = self.request.user
        
        # Citizens can only see their own incidents
        if user.role == 'CITIZEN':
            return Incident.objects.filter(reported_by=user)
        
        # Responders and command can see all incidents
        return Incident.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return IncidentUpdateSerializer
        return IncidentSerializer


class IncidentMediaView(generics.ListCreateAPIView):
    """List and create media for an incident."""
    serializer_class = IncidentMediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        incident_id = self.kwargs['incident_id']
        incident = get_object_or_404(Incident, incident_id=incident_id)
        
        # Check permissions
        user = self.request.user
        if user.role == 'CITIZEN' and incident.reported_by != user:
            return IncidentMedia.objects.none()
        
        return IncidentMedia.objects.filter(incident=incident)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IncidentMediaCreateSerializer
        return IncidentMediaSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['incident'] = get_object_or_404(Incident, incident_id=self.kwargs['incident_id'])
        return context


class IncidentNoteView(generics.ListCreateAPIView):
    """List and create notes for an incident."""
    serializer_class = IncidentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        incident_id = self.kwargs['incident_id']
        incident = get_object_or_404(Incident, incident_id=incident_id)
        
        # Check permissions
        user = self.request.user
        if user.role == 'CITIZEN':
            # Citizens can only see non-internal notes
            return IncidentNote.objects.filter(incident=incident, is_internal=False)
        
        # Responders and command can see all notes
        return IncidentNote.objects.filter(incident=incident)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IncidentNoteCreateSerializer
        return IncidentNoteSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['incident'] = get_object_or_404(Incident, incident_id=self.kwargs['incident_id'])
        return context


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_incident_status(request, incident_id):
    """Update incident status with validation and history tracking."""
    incident = get_object_or_404(Incident, incident_id=incident_id)
    user = request.user
    
    # Check permissions
    if user.role == 'CITIZEN' and incident.reported_by != user:
        return Response(
            {'error': 'You can only update incidents you reported'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    new_status = request.data.get('status')
    notes = request.data.get('notes', '')
    
    if not new_status:
        return Response(
            {'error': 'Status is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate status transition
    old_status = incident.status
    valid_transitions = {
        'NEW': ['TRIAGED', 'CLOSED'],
        'TRIAGED': ['DISPATCHED', 'CLOSED'],
        'DISPATCHED': ['ONGOING', 'CLOSED'],
        'ONGOING': ['RESOLVED', 'CLOSED'],
        'RESOLVED': ['CLOSED'],
        'CLOSED': []
    }
    
    if new_status not in valid_transitions.get(old_status, []):
        return Response(
            {'error': f'Invalid status transition from {old_status} to {new_status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update status and timestamps
    incident.status = new_status
    now = timezone.now()
    
    if new_status == 'TRIAGED' and not incident.triaged_at:
        incident.triaged_at = now
    elif new_status == 'DISPATCHED' and not incident.dispatched_at:
        incident.dispatched_at = now
    elif new_status == 'RESOLVED' and not incident.resolved_at:
        incident.resolved_at = now
    elif new_status == 'CLOSED' and not incident.closed_at:
        incident.closed_at = now
    
    incident.save()
    
    # Create status history
    IncidentStatusHistory.objects.create(
        incident=incident,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        notes=notes
    )
    
    return Response({
        'message': f'Incident status updated to {new_status}',
        'incident': IncidentSerializer(incident).data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_statistics(request):
    """Get incident statistics for dashboard."""
    user = request.user
    
    # Base queryset based on user role
    if user.role == 'CITIZEN':
        base_queryset = Incident.objects.filter(reported_by=user)
    else:
        base_queryset = Incident.objects.all()
    
    # Time-based filters
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Statistics
    stats = {
        'total_incidents': base_queryset.count(),
        'active_incidents': base_queryset.filter(status__in=['NEW', 'TRIAGED', 'DISPATCHED', 'ONGOING']).count(),
        'resolved_incidents': base_queryset.filter(status='RESOLVED').count(),
        'closed_incidents': base_queryset.filter(status='CLOSED').count(),
        
        'today': base_queryset.filter(created_at__date=today).count(),
        'this_week': base_queryset.filter(created_at__date__gte=week_ago).count(),
        'this_month': base_queryset.filter(created_at__date__gte=month_ago).count(),
        
        'by_category': base_queryset.values('category').annotate(count=Count('id')),
        'by_severity': base_queryset.values('severity').annotate(count=Count('id')),
        'by_status': base_queryset.values('status').annotate(count=Count('id')),
    }
    
    # Average response time (only for dispatched incidents)
    dispatched_incidents = base_queryset.filter(
        status__in=['DISPATCHED', 'ONGOING', 'RESOLVED', 'CLOSED'],
        dispatched_at__isnull=False
    )
    
    if dispatched_incidents.exists():
        avg_response_time = dispatched_incidents.aggregate(
            avg_time=Avg('dispatched_at' - 'created_at')
        )['avg_time']
        stats['avg_response_time_seconds'] = avg_response_time.total_seconds() if avg_response_time else 0
    else:
        stats['avg_response_time_seconds'] = 0
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nearby_incidents(request):
    """Find incidents near a specific location."""
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    radius_km = float(request.query_params.get('radius', 10))  # Default 10km radius
    
    if not lat or not lon:
        return Response(
            {'error': 'Latitude and longitude are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Convert to Point and find incidents within radius
    point = Point(float(lon), float(lat))
    
    # Simple distance calculation (approximate)
    # In production, use PostGIS ST_DWithin for accurate geographic queries
    incidents = Incident.objects.filter(
        lat__range=(float(lat) - radius_km/111, float(lat) + radius_km/111),
        lon__range=(float(lon) - radius_km/111, float(lon) + radius_km/111)
    )[:50]  # Limit results
    
    serializer = IncidentListSerializer(incidents, many=True)
    return Response(serializer.data)
