# DMERS - Disaster Management & Emergency Response System

A comprehensive, full-stack emergency response management system built with Django, PostgreSQL, MongoDB, and React.

## Group Memmbers
- 191250 - Ng'ang'a Allan Ngugi
- 152585 - Vansh Panara
- 192483 - Michael Asingwire
- 192992 - Ziki Mtula
- 189728 - Boniface Mwangi
- 180761 - Macharia Daniel
- 184304 - Emmanuel Kisoso

## Features

### Core Functionality
- **Incident Management**: Report, track, and manage emergency incidents
- **Response Coordination**: Dispatch and track emergency response units
- **Shelter Management**: Manage emergency shelters and capacity
- **Inventory Tracking**: Track supplies and equipment across locations
- **Real-time Analytics**: Data warehouse with comprehensive reporting
- **XML Integration**: Import/export incidents via standardized XML format

### User Roles
- **Citizens**: Report incidents and track status
- **Responders**: Accept dispatches and send situation reports
- **Command Center**: Coordinate response operations
- **Administrators**: System management and oversight

### Technical Features
- **Multi-Database Architecture**: PostgreSQL for operational data, MongoDB for unstructured data
- **PostGIS Integration**: Advanced geographic queries and spatial analysis
- **Data Warehouse**: Star schema design with ETL pipeline
- **RESTful API**: Comprehensive API for all system operations
- **Real-time Updates**: WebSocket support for live updates
- **Mobile Responsive**: Modern React frontend with Tailwind CSS

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Django Backend │    │   PostgreSQL    │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    MongoDB      │
                       │   (Port 27017)  │
                       └─────────────────┘
```

## Prerequisites

- Python 3.11+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL 15+ with PostGIS
- MongoDB 7.0+
- Redis 7.0+

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DMERS
```

### 2. Start Services with Docker

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Setup Django Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python seed_data.py

# Start Django server
python manage.py runserver
```

### 4. Setup React Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 5. Access the System

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/

## Default Credentials

After running the seed data script:

- **Admin**: `admin@dmers.org` / `admin123`
- **Command**: `command@dmers.org` / `command123`
- **Responder**: `medic1@dmers.org` / `responder123`
- **Citizen**: `citizen1@dmers.org` / `citizen123`

## Database Schema

### PostgreSQL (Operational Data)

#### Core Tables
- `app_user` - User accounts and roles
- `incident` - Emergency incidents with PostGIS support
- `responder_unit` - Emergency response units
- `dispatch` - Unit dispatch records
- `shelter` - Emergency shelter locations
- `item` - Inventory items
- `shelter_stock` - Stock levels per shelter

#### Analytics Tables (Data Warehouse)
- `dim_date` - Date dimension for time analysis
- `dim_region` - Geographic region dimension
- `dim_incident` - Incident dimension
- `dim_unit` - Response unit dimension
- `fact_incident_daily` - Daily incident facts
- `fact_response` - Response performance facts
- `fact_shelter_utilization` - Shelter capacity facts
- `fact_inventory` - Supply chain facts

### MongoDB Collections

- `citizen_reports` - Citizen incident reports with geospatial indexing
- `situation_reports` - Responder situation reports
- `telemetry` - Unit GPS and sensor data (TTL indexed)

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Current user info

### Incidents
- `GET /api/incidents/` - List incidents
- `POST /api/incidents/` - Create incident
- `GET /api/incidents/{id}/` - Get incident details
- `PUT /api/incidents/{id}/` - Update incident
- `POST /api/incidents/{id}/status/` - Update incident status

### Responders
- `GET /api/responders/units/` - List response units
- `GET /api/responders/dispatches/` - List dispatches
- `POST /api/responders/dispatches/` - Create dispatch

### Logistics
- `GET /api/logistics/shelters/` - List shelters
- `GET /api/logistics/inventory/` - List inventory
- `POST /api/logistics/stock/` - Update stock levels

### Analytics
- `GET /api/analytics/dashboard/` - Dashboard summary
- `GET /api/analytics/incidents/trends/` - Incident trends
- `GET /api/analytics/regional/analysis/` - Regional analysis
- `GET /api/analytics/response/performance/` - Response metrics

### XML Integration
- `POST /api/xml/import-incident/` - Import incident from XML
- `GET /api/xml/export-incident/{id}/` - Export incident to XML
- `GET /api/xml/schema/` - Get XSD schema
- `POST /api/xml/validate/` - Validate XML content

## ETL Pipeline

The system includes a comprehensive ETL pipeline for populating the data warehouse:

```python
# Run daily ETL
python manage.py shell
from analytics.etl import run_daily_etl
run_daily_etl()

# Run custom ETL for date range
from analytics.etl import run_etl_job
from datetime import date
run_etl_job(date(2024, 1, 1), date(2024, 1, 31))
```

## Geographic Features

- **PostGIS Integration**: Advanced spatial queries and analysis
- **Geospatial Indexing**: Efficient location-based searches
- **Distance Calculations**: Automatic proximity analysis
- **Boundary Management**: Geographic area definitions

## Frontend Components

### Core Pages
- **Dashboard**: Overview with live map and key metrics
- **Incidents**: Incident management and triage board
- **Responders**: Unit status and dispatch management
- **Shelters**: Shelter capacity and inventory
- **Analytics**: Data visualization and reporting

### Key Components
- **IncidentMap**: Interactive map with incident markers
- **StatCard**: Metric display cards
- **RecentIncidents**: Latest incident list
- **StatusBadge**: Incident status indicators
- **ChartComponents**: Analytics visualizations

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
POSTGRES_DB=dmers_db
POSTGRES_USER=dmers_user
POSTGRES_PASSWORD=dmers_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB Settings
MONGODB_URI=mongodb://dmers_user:dmers_password@localhost:27017/dmers_mongo

# Redis Settings
REDIS_URL=redis://localhost:6379/0
```

### Django Settings

Key settings in `dmers/settings.py`:

- **Database Configuration**: PostgreSQL with PostGIS
- **MongoDB Integration**: Direct MongoDB connection
- **REST Framework**: API configuration and permissions
- **CORS Settings**: Frontend integration
- **Authentication**: Token-based authentication

## Testing

### Backend Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test incidents
python manage.py test responders
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Performance Optimization

### Database Optimization
- **Indexing**: Strategic indexes on frequently queried fields
- **Partitioning**: Monthly partitioning for incident tables
- **Query Optimization**: Efficient joins and aggregations

### Caching Strategy
- **Redis Caching**: Session and query result caching
- **Database Query Caching**: Frequently accessed data
- **Frontend Caching**: API response caching

## Production Deployment

### Security Considerations
- **HTTPS**: SSL/TLS encryption
- **Authentication**: JWT tokens with refresh
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries

### Scaling Considerations
- **Load Balancing**: Multiple Django instances
- **Database Clustering**: PostgreSQL read replicas
- **CDN**: Static file delivery
- **Monitoring**: Application performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the API docs at `/api/docs/`
- **Community**: Join our discussion forum

## Roadmap

### Phase 2 Features
- **Real-time Notifications**: WebSocket-based alerts
- **Mobile App**: Native mobile applications
- **AI Integration**: Predictive analytics and automation
- **IoT Integration**: Sensor data integration
- **Advanced Reporting**: Custom report builder

### Phase 3 Features
- **Multi-tenant Support**: Organization isolation
- **API Marketplace**: Third-party integrations
- **Advanced Analytics**: Machine learning insights
- **Disaster Simulation**: Training and planning tools

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB
- **Network**: 100Mbps

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps+

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check MongoDB status
sudo systemctl status mongod

# Verify connection strings in .env
```

#### Migration Errors
```bash
# Reset migrations
python manage.py migrate --fake-initial

# Check migration status
python manage.py showmigrations
```

#### Frontend Build Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [React Documentation](https://reactjs.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

---

**DMERS** - Empowering emergency response through technology and innovation.
