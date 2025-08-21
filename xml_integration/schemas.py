"""
XSD Schema for DMERS Incident Exchange
Defines the structure for importing/exporting incident data via XML
"""

INCIDENT_XSD_SCHEMA = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" 
           xmlns:dmers="http://dmers.org/schema/v1.0"
           targetNamespace="http://dmers.org/schema/v1.0"
           elementFormDefault="qualified">

    <!-- Incident Root Element -->
    <xs:element name="Incident">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="ID" type="xs:string" minOccurs="1" maxOccurs="1"/>
                <xs:element name="CreatedAt" type="xs:dateTime" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Category" type="dmers:IncidentCategory" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Severity" type="dmers:SeverityLevel" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Status" type="dmers:IncidentStatus" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Location" type="dmers:Location" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Summary" type="xs:string" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Description" type="xs:string" minOccurs="0" maxOccurs="1"/>
                <xs:element name="Reporter" type="dmers:Reporter" minOccurs="1" maxOccurs="1"/>
                <xs:element name="Tags" type="dmers:Tags" minOccurs="0" maxOccurs="1"/>
                <xs:element name="Media" type="dmers:Media" minOccurs="0" maxOccurs="1"/>
                <xs:element name="Notes" type="dmers:Notes" minOccurs="0" maxOccurs="1"/>
            </xs:sequence>
            <xs:attribute name="version" type="xs:string" default="1.0"/>
            <xs:attribute name="source" type="xs:string"/>
        </xs:complexType>
    </xs:element>

    <!-- Incident Categories -->
    <xs:simpleType name="IncidentCategory">
        <xs:restriction base="xs:string">
            <xs:enumeration value="FIRE"/>
            <xs:enumeration value="FLOOD"/>
            <xs:enumeration value="ACCIDENT"/>
            <xs:enumeration value="VIOLENCE"/>
            <xs:enumeration value="MEDICAL"/>
            <xs:enumeration value="NATURAL"/>
            <xs:enumeration value="OTHER"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- Severity Levels -->
    <xs:simpleType name="SeverityLevel">
        <xs:restriction base="xs:integer">
            <xs:minInclusive value="1"/>
            <xs:maxInclusive value="5"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- Incident Status -->
    <xs:simpleType name="IncidentStatus">
        <xs:restriction base="xs:string">
            <xs:enumeration value="NEW"/>
            <xs:enumeration value="TRIAGED"/>
            <xs:enumeration value="DISPATCHED"/>
            <xs:enumeration value="ONGOING"/>
            <xs:enumeration value="RESOLVED"/>
            <xs:enumeration value="CLOSED"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- Location Information -->
    <xs:complexType name="Location">
        <xs:sequence>
            <xs:element name="Latitude" type="xs:decimal" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Longitude" type="xs:decimal" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Address" type="xs:string" minOccurs="0" maxOccurs="1"/>
            <xs:element name="Area" type="dmers:Area" minOccurs="0" maxOccurs="1"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Area Information -->
    <xs:complexType name="Area">
        <xs:sequence>
            <xs:element name="Code" type="xs:string" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Name" type="xs:string" minOccurs="1" maxOccurs="1"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Reporter Information -->
    <xs:complexType name="Reporter">
        <xs:sequence>
            <xs:element name="FullName" type="xs:string" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Email" type="xs:email" minOccurs="0" maxOccurs="1"/>
            <xs:element name="Phone" type="xs:string" minOccurs="0" maxOccurs="1"/>
            <xs:element name="Role" type="dmers:UserRole" minOccurs="1" maxOccurs="1"/>
        </xs:sequence>
    </xs:complexType>

    <!-- User Roles -->
    <xs:simpleType name="UserRole">
        <xs:restriction base="xs:string">
            <xs:enumeration value="CITIZEN"/>
            <xs:enumeration value="RESPONDER"/>
            <xs:enumeration value="COMMAND"/>
            <xs:enumeration value="ADMIN"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- Tags -->
    <xs:complexType name="Tags">
        <xs:sequence>
            <xs:element name="Tag" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Media -->
    <xs:complexType name="Media">
        <xs:sequence>
            <xs:element name="File" type="dmers:MediaFile" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Media File -->
    <xs:complexType name="MediaFile">
        <xs:sequence>
            <xs:element name="URL" type="xs:anyURI" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Type" type="dmers:MediaType" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Caption" type="xs:string" minOccurs="0" maxOccurs="1"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Media Types -->
    <xs:simpleType name="MediaType">
        <xs:restriction base="xs:string">
            <xs:enumeration value="IMAGE"/>
            <xs:enumeration value="VIDEO"/>
            <xs:enumeration value="AUDIO"/>
            <xs:enumeration value="DOCUMENT"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- Notes -->
    <xs:complexType name="Notes">
        <xs:sequence>
            <xs:element name="Note" type="dmers:Note" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Note -->
    <xs:complexType name="Note">
        <xs:sequence>
            <xs:element name="Content" type="xs:string" minOccurs="1" maxOccurs="1"/>
            <xs:element name="Author" type="xs:string" minOccurs="1" maxOccurs="1"/>
            <xs:element name="CreatedAt" type="xs:dateTime" minOccurs="1" maxOccurs="1"/>
            <xs:element name="IsInternal" type="xs:boolean" minOccurs="0" maxOccurs="1" default="false"/>
        </xs:sequence>
    </xs:complexType>

    <!-- Email type for validation -->
    <xs:simpleType name="email">
        <xs:restriction base="xs:string">
            <xs:pattern value="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"/>
        </xs:restriction>
    </xs:simpleType>

</xs:schema>'''

# Sample XML template for incident export
INCIDENT_XML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<dmers:Incident xmlns:dmers="http://dmers.org/schema/v1.0" version="1.0" source="DMERS">
    <dmers:ID>{incident_id}</dmers:ID>
    <dmers:CreatedAt>{created_at}</dmers:CreatedAt>
    <dmers:Category>{category}</dmers:Category>
    <dmers:Severity>{severity}</dmers:Severity>
    <dmers:Status>{status}</dmers:Status>
    <dmers:Location>
        <dmers:Latitude>{lat}</dmers:Latitude>
        <dmers:Longitude>{lon}</dmers:Longitude>
        <dmers:Address>{address}</dmers:Address>
        <dmers:Area>
            <dmers:Code>{area_code}</dmers:Code>
            <dmers:Name>{area_name}</dmers:Name>
        </dmers:Area>
    </dmers:Location>
    <dmers:Summary>{summary}</dmers:Summary>
    <dmers:Description>{description}</dmers:Description>
    <dmers:Reporter>
        <dmers:FullName>{reporter_name}</dmers:FullName>
        <dmers:Email>{reporter_email}</dmers:Email>
        <dmers:Phone>{reporter_phone}</dmers:Phone>
        <dmers:Role>{reporter_role}</dmers:Role>
    </dmers:Reporter>
    <dmers:Tags>
        {tags}
    </dmers:Tags>
    <dmers:Media>
        {media}
    </dmers:Media>
    <dmers:Notes>
        {notes}
    </dmers:Notes>
</dmers:Incident>'''
