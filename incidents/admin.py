from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Area, Incident, IncidentStatusHistory, IncidentMedia, IncidentNote


@admin.register(Area)
class AreaAdmin(OSMGeoAdmin):
    """Admin configuration for Area model with map support."""
    
    list_display = ('name', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'code', 'description')}),
        ('Geographic Data', {'fields': ('boundary', 'center')}),
    )


@admin.register(Incident)
class IncidentAdmin(OSMGeoAdmin):
    """Admin configuration for Incident model with map support."""
    
    list_display = ('incident_id', 'category', 'severity', 'status', 'area', 'reported_by', 'created_at')
    list_filter = ('category', 'severity', 'status', 'area', 'created_at')
    search_fields = ('incident_id', 'summary', 'description', 'reported_by__full_name', 'area__name')
    ordering = ('-created_at',)
    readonly_fields = ('incident_id', 'created_at', 'updated_at', 'priority_score')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('incident_id', 'category', 'severity', 'status', 'summary', 'description')
        }),
        ('Location', {
            'fields': ('area', 'lat', 'lon', 'location', 'address')
        }),
        ('Reporting', {
            'fields': ('reported_by', 'tags', 'priority_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'triaged_at', 'dispatched_at', 'resolved_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reported_by', 'area')


@admin.register(IncidentStatusHistory)
class IncidentStatusHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for IncidentStatusHistory model."""
    
    list_display = ('incident', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('incident__incident_id', 'changed_by__full_name', 'notes')
    ordering = ('-changed_at',)
    readonly_fields = ('changed_at',)
    
    fieldsets = (
        ('Status Change', {'fields': ('incident', 'old_status', 'new_status')}),
        ('Details', {'fields': ('changed_by', 'notes', 'changed_at')}),
    )


@admin.register(IncidentMedia)
class IncidentMediaAdmin(admin.ModelAdmin):
    """Admin configuration for IncidentMedia model."""
    
    list_display = ('incident', 'media_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('media_type', 'uploaded_at')
    search_fields = ('incident__incident_id', 'caption', 'uploaded_by__full_name')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Media Information', {'fields': ('incident', 'media_type', 'file', 'caption')}),
        ('Upload Details', {'fields': ('uploaded_by', 'uploaded_at')}),
    )


@admin.register(IncidentNote)
class IncidentNoteAdmin(admin.ModelAdmin):
    """Admin configuration for IncidentNote model."""
    
    list_display = ('incident', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('incident__incident_id', 'author__full_name', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Note Content', {'fields': ('incident', 'content', 'is_internal')}),
        ('Metadata', {'fields': ('author', 'created_at', 'updated_at')}),
    )
