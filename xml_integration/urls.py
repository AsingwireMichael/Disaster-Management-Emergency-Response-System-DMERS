from django.urls import path
from . import views

app_name = 'xml_integration'

urlpatterns = [
    path('import-incident/', views.import_incident, name='import_incident'),
    path('export-incident/<uuid:incident_id>/', views.export_incident, name='export_incident'),
    path('schema/', views.get_xsd_schema, name='get_schema'),
    path('validate/', views.validate_xml, name='validate_xml'),
]
