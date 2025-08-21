from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from lxml import etree
import xmltodict
import json
from incidents.models import Incident, Area
from users.models import User
from .schemas import INCIDENT_XSD_SCHEMA, INCIDENT_XML_TEMPLATE


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_incident(request):
    """Import incident from XML format."""
    try:
        # Get XML content from request
        xml_content = request.data.get('xml_content')
        if not xml_content:
            return Response(
                {'error': 'XML content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate XML against XSD schema
        try:
            schema_doc = etree.fromstring(INCIDENT_XSD_SCHEMA.encode('utf-8'))
            schema = etree.XMLSchema(schema_doc)
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            schema.assertValid(xml_doc)
        except etree.DocumentInvalid as e:
            return Response(
                {'error': f'XML validation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'XML parsing error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse XML to dictionary
        try:
            incident_data = xmltodict.parse(xml_content)
            incident_root = incident_data.get('dmers:Incident', incident_data.get('Incident', {}))
        except Exception as e:
            return Response(
                {'error': f'XML parsing failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract incident information
        try:
            # Basic incident data
            incident_id = incident_root.get('ID')
            category = incident_root.get('Category')
            severity = int(incident_root.get('Severity', 1))
            status = incident_root.get('Status', 'NEW')
            summary = incident_root.get('Summary')
            description = incident_root.get('Description', '')
            
            # Location data
            location = incident_root.get('Location', {})
            lat = float(location.get('Latitude', 0))
            lon = float(location.get('Longitude', 0))
            address = location.get('Address', '')
            
            # Area data
            area_info = location.get('Area', {})
            area_code = area_info.get('Code')
            area_name = area_info.get('Name')
            
            # Reporter data
            reporter_info = incident_root.get('Reporter', {})
            reporter_name = reporter_info.get('FullName')
            reporter_email = reporter_info.get('Email')
            reporter_phone = reporter_info.get('Phone')
            reporter_role = reporter_info.get('Role', 'CITIZEN')
            
            # Tags
            tags_data = incident_root.get('Tags', {})
            tags = tags_data.get('Tag', []) if isinstance(tags_data.get('Tag'), list) else [tags_data.get('Tag')] if tags_data.get('Tag') else []
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Data extraction failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        if not all([incident_id, category, summary, lat, lon, reporter_name]):
            return Response(
                {'error': 'Missing required fields: ID, Category, Summary, Location, Reporter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create area
        area, created = Area.objects.get_or_create(
            code=area_code or 'UNKNOWN',
            defaults={
                'name': area_name or 'Unknown Area',
                'description': f'Area for incident {incident_id}'
            }
        )
        
        # Get or create reporter user
        if reporter_email:
            reporter, created = User.objects.get_or_create(
                email=reporter_email,
                defaults={
                    'full_name': reporter_name,
                    'phone': reporter_phone or '',
                    'role': reporter_role,
                    'is_active': True
                }
            )
        else:
            # Create temporary user if no email
            reporter = User.objects.create(
                email=f"temp_{incident_id}@dmers.local",
                full_name=reporter_name,
                phone=reporter_phone or '',
                role=reporter_role,
                is_active=True
            )
        
        # Create incident
        incident = Incident.objects.create(
            incident_id=incident_id,
            reported_by=reporter,
            area=area,
            category=category,
            severity=severity,
            status=status,
            lat=lat,
            lon=lon,
            address=address,
            summary=summary,
            description=description,
            tags=tags
        )
        
        # Process media if present
        media_data = incident_root.get('Media', {})
        if media_data and 'File' in media_data:
            media_files = media_data['File'] if isinstance(media_data['File'], list) else [media_data['File']]
            # Note: Media files would need to be downloaded and stored
            # This is a simplified implementation
        
        # Process notes if present
        notes_data = incident_root.get('Notes', {})
        if notes_data and 'Note' in notes_data:
            notes = notes_data['Note'] if isinstance(notes_data['Note'], list) else [notes_data['Note']]
            # Note: Notes would be created here
            # This is a simplified implementation
        
        return Response({
            'message': 'Incident imported successfully',
            'incident_id': incident.incident_id,
            'status': 'imported'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Import failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_incident(request, incident_id):
    """Export incident to XML format."""
    try:
        # Get incident
        incident = get_object_or_404(Incident, incident_id=incident_id)
        
        # Check permissions
        user = request.user
        if user.role == 'CITIZEN' and incident.reported_by != user:
            return Response(
                {'error': 'You can only export incidents you reported'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prepare data for XML template
        tags_xml = ''
        if incident.tags:
            for tag in incident.tags:
                tags_xml += f'        <dmers:Tag>{tag}</dmers:Tag>\n'
        
        media_xml = ''
        if incident.media.exists():
            for media_item in incident.media.all():
                media_xml += f'''        <dmers:File>
            <dmers:URL>{media_item.file.url}</dmers:URL>
            <dmers:Type>{media_item.media_type}</dmers:Type>
            <dmers:Caption>{media_item.caption or ''}</dmers:Caption>
        </dmers:File>\n'''
        
        notes_xml = ''
        if incident.notes.exists():
            for note in incident.notes.all():
                notes_xml += f'''        <dmers:Note>
            <dmers:Content>{note.content}</dmers:Content>
            <dmers:Author>{note.author.full_name}</dmers:Author>
            <dmers:CreatedAt>{note.created_at.isoformat()}</dmers:CreatedAt>
            <dmers:IsInternal>{str(note.is_internal).lower()}</dmers:IsInternal>
        </dmers:Note>\n'''
        
        # Generate XML
        xml_content = INCIDENT_XML_TEMPLATE.format(
            incident_id=incident.incident_id,
            created_at=incident.created_at.isoformat(),
            category=incident.category,
            severity=incident.severity,
            status=incident.status,
            lat=incident.lat,
            lon=incident.lon,
            address=incident.address or '',
            area_code=incident.area.code,
            area_name=incident.area.name,
            summary=incident.summary,
            description=incident.description or '',
            reporter_name=incident.reported_by.full_name,
            reporter_email=incident.reported_by.email,
            reporter_phone=incident.reported_by.phone,
            reporter_role=incident.reported_by.role,
            tags=tags_xml,
            media=media_xml,
            notes=notes_xml
        )
        
        # Return XML response
        response = HttpResponse(xml_content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="incident_{incident_id}.xml"'
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Export failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_xsd_schema(request):
    """Get the XSD schema for incident validation."""
    try:
        response = HttpResponse(INCIDENT_XSD_SCHEMA, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="incident_schema.xsd"'
        return response
    except Exception as e:
        return Response(
            {'error': f'Schema retrieval failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_xml(request):
    """Validate XML content against the XSD schema."""
    try:
        xml_content = request.data.get('xml_content')
        if not xml_content:
            return Response(
                {'error': 'XML content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate XML against XSD schema
        try:
            schema_doc = etree.fromstring(INCIDENT_XSD_SCHEMA.encode('utf-8'))
            schema = etree.XMLSchema(schema_doc)
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            schema.assertValid(xml_doc)
            
            return Response({
                'message': 'XML is valid',
                'valid': True
            })
            
        except etree.DocumentInvalid as e:
            return Response({
                'message': 'XML validation failed',
                'valid': False,
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'message': 'XML parsing error',
                'valid': False,
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': f'Validation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
