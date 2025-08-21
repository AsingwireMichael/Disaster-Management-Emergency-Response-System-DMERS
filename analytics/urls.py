from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard and summary
    path('dashboard/', views.dashboard_summary, name='dashboard_summary'),
    
    # Analysis endpoints
    path('incidents/trends/', views.incident_trends, name='incident_trends'),
    path('regional/analysis/', views.regional_analysis, name='regional_analysis'),
    path('response/performance/', views.response_performance, name='response_performance'),
    path('inventory/analysis/', views.inventory_analysis, name='inventory_analysis'),
    
    # ETL management
    path('etl/trigger/', views.trigger_etl, name='trigger_etl'),
]
