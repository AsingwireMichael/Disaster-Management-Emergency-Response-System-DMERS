from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Area, Incident, IncidentStatusHistory, IncidentMedia, IncidentNote

User = get_user_model()


class AreaSerializer(serializers.ModelSerializer):
    """Serializer for Area model."""
    
    class Meta:
        model = Area
        fields = ['id', 'name', 'code', 'description', 'center', 'created_at']


class IncidentMediaSerializer(serializers.ModelSerializer):
    """Serializer for IncidentMedia model."""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    
    class Meta:
        model = IncidentMedia
        fields = [
            'id', 'media_type', 'file', 'caption', 'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']


class IncidentNoteSerializer(serializers.ModelSerializer):
    """Serializer for IncidentNote model."""
    
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    
    class Meta:
        model = IncidentNote
        fields = [
            'id', 'content', 'is_internal', 'author', 'author_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']


class IncidentStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for IncidentStatusHistory model."""
    
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    
    class Meta:
        model = IncidentStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'changed_by', 'changed_by_name', 'changed_at', 'notes'
        ]
        read_only_fields = ['changed_at']


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for Incident model."""
    
    area = AreaSerializer(read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    media = IncidentMediaSerializer(many=True, read_only=True)
    notes = IncidentNoteSerializer(many=True, read_only=True)
    status_history = IncidentStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'incident_id', 'created_at', 'updated_at', 'reported_by', 'reported_by_name',
            'area', 'category', 'category_display', 'severity', 'status', 'status_display',
            'lat', 'lon', 'location', 'address', 'summary', 'description', 'tags',
            'triaged_at', 'dispatched_at', 'resolved_at', 'closed_at', 'priority_score',
            'media', 'notes', 'status_history'
        ]
        read_only_fields = [
            'incident_id', 'created_at', 'updated_at', 'priority_score', 'media', 'notes', 'status_history'
        ]


class IncidentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new incidents."""
    
    class Meta:
        model = Incident
        fields = [
            'area', 'category', 'severity', 'lat', 'lon', 'address', 'summary', 'description', 'tags'
        ]
    
    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class IncidentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating incidents."""
    
    class Meta:
        model = Incident
        fields = [
            'category', 'severity', 'status', 'summary', 'description', 'tags',
            'triaged_at', 'dispatched_at', 'resolved_at', 'closed_at'
        ]
    
    def validate(self, attrs):
        # Validate status transitions
        instance = self.instance
        if instance and 'status' in attrs:
            new_status = attrs['status']
            old_status = instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'NEW': ['TRIAGED', 'CLOSED'],
                'TRIAGED': ['DISPATCHED', 'CLOSED'],
                'DISPATCHED': ['ONGOING', 'CLOSED'],
                'ONGOING': ['RESOLVED', 'CLOSED'],
                'RESOLVED': ['CLOSED'],
                'CLOSED': []
            }
            
            if new_status not in valid_transitions.get(old_status, []):
                raise serializers.ValidationError(
                    f"Invalid status transition from {old_status} to {new_status}"
                )
        
        return attrs


class IncidentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for incident lists."""
    
    area_name = serializers.CharField(source='area.name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'incident_id', 'created_at', 'category', 'category_display', 'severity',
            'status', 'status_display', 'area_name', 'reported_by_name', 'summary',
            'lat', 'lon', 'priority_score'
        ]


class IncidentMediaCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating incident media."""
    
    class Meta:
        model = IncidentMedia
        fields = ['media_type', 'file', 'caption']
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['incident'] = self.context['incident']
        return super().create(validated_data)


class IncidentNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating incident notes."""
    
    class Meta:
        model = IncidentNote
        fields = ['content', 'is_internal']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['incident'] = self.context['incident']
        return super().create(validated_data)
