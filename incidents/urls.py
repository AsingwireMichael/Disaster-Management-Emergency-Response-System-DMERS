from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    # Area endpoints
    path('areas/', views.AreaListView.as_view(), name='area_list'),
    
    # Incident endpoints
    path('incidents/', views.IncidentListView.as_view(), name='incident_list'),
    path('incidents/<uuid:incident_id>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<uuid:incident_id>/status/', views.update_incident_status, name='update_incident_status'),
    path('incidents/<uuid:incident_id>/media/', views.IncidentMediaView.as_view(), name='incident_media'),
    path('incidents/<uuid:incident_id>/notes/', views.IncidentNoteView.as_view(), name='incident_notes'),
    
    # Analytics endpoints
    path('incidents/statistics/', views.incident_statistics, name='incident_statistics'),
    path('incidents/nearby/', views.nearby_incidents, name='nearby_incidents'),
]
