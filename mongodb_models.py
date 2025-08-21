"""
MongoDB Models for DMERS
Handles citizen reports, situation reports, and telemetry data
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manager for MongoDB operations."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(settings.MONGODB_URI)
            self.db = self.client.get_default_database()
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection."""
        return self.db[collection_name]


class CitizenReport:
    """MongoDB model for citizen reports."""
    
    def __init__(self, db_manager):
        self.collection = db_manager.get_collection('citizen_reports')
        self.setup_indexes()
    
    def setup_indexes(self):
        """Setup MongoDB indexes for citizen reports."""
        try:
            # 2dsphere index for geospatial queries
            self.collection.create_index([("geo", "2dsphere")])
            
            # Index on incident ID for quick lookups
            self.collection.create_index([("incidentId", ASCENDING)])
            
            # Index on reported time for time-based queries
            self.collection.create_index([("reportedAt", DESCENDING)])
            
            # Index on status for filtering
            self.collection.create_index([("status", ASCENDING)])
            
            # Compound index for efficient queries
            self.collection.create_index([
                ("status", ASCENDING),
                ("reportedAt", DESCENDING),
                ("incidentId", ASCENDING)
            ])
            
            logger.info("Citizen reports indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create citizen reports indexes: {str(e)}")
    
    def create_report(self, report_data):
        """Create a new citizen report."""
        try:
            # Add timestamp
            report_data['reportedAt'] = datetime.utcnow()
            report_data['status'] = 'INGESTED'
            
            # Insert document
            result = self.collection.insert_one(report_data)
            
            logger.info(f"Citizen report created with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create citizen report: {str(e)}")
            raise
    
    def get_report(self, report_id):
        """Get a citizen report by ID."""
        try:
            from bson import ObjectId
            report = self.collection.find_one({"_id": ObjectId(report_id)})
            return report
        except Exception as e:
            logger.error(f"Failed to get citizen report: {str(e)}")
            return None
    
    def update_report_status(self, report_id, new_status, notes=None):
        """Update the status of a citizen report."""
        try:
            from bson import ObjectId
            update_data = {"status": new_status}
            if notes:
                update_data["statusNotes"] = notes
            
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Citizen report {report_id} status updated to {new_status}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update citizen report status: {str(e)}")
            return False
    
    def get_reports_by_incident(self, incident_id):
        """Get all reports for a specific incident."""
        try:
            reports = list(self.collection.find({"incidentId": incident_id}))
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports by incident: {str(e)}")
            return []
    
    def get_reports_by_location(self, lat, lon, radius_km=10):
        """Get reports within a radius of a location."""
        try:
            # MongoDB geospatial query
            query = {
                "geo": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "$maxDistance": radius_km * 1000  # Convert to meters
                    }
                }
            }
            
            reports = list(self.collection.find(query).limit(100))
            return reports
            
        except Exception as e:
            logger.error(f"Failed to get reports by location: {str(e)}")
            return []
    
    def get_reports_by_status(self, status, limit=100):
        """Get reports by status."""
        try:
            reports = list(self.collection.find({"status": status}).limit(limit))
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports by status: {str(e)}")
            return []


class SituationReport:
    """MongoDB model for situation reports."""
    
    def __init__(self, db_manager):
        self.collection = db_manager.get_collection('situation_reports')
        self.setup_indexes()
    
    def setup_indexes(self):
        """Setup MongoDB indexes for situation reports."""
        try:
            # Index on dispatch ID for quick lookups
            self.collection.create_index([("dispatchId", ASCENDING)])
            
            # Index on reporter for user-based queries
            self.collection.create_index([("reporter.userId", ASCENDING)])
            
            # Index on created time for time-based queries
            self.collection.create_index([("createdAt", DESCENDING)])
            
            # Index on unit for unit-based queries
            self.collection.create_index([("unitId", ASCENDING)])
            
            # Compound index for efficient queries
            self.collection.create_index([
                ("dispatchId", ASCENDING),
                ("createdAt", DESCENDING)
            ])
            
            logger.info("Situation reports indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create situation reports indexes: {str(e)}")
    
    def create_report(self, report_data):
        """Create a new situation report."""
        try:
            # Add timestamp
            report_data['createdAt'] = datetime.utcnow()
            report_data['updatedAt'] = datetime.utcnow()
            
            # Insert document
            result = self.collection.insert_one(report_data)
            
            logger.info(f"Situation report created with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create situation report: {str(e)}")
            raise
    
    def get_report(self, report_id):
        """Get a situation report by ID."""
        try:
            from bson import ObjectId
            report = self.collection.find_one({"_id": ObjectId(report_id)})
            return report
        except Exception as e:
            logger.error(f"Failed to get situation report: {str(e)}")
            return None
    
    def update_report(self, report_id, update_data):
        """Update a situation report."""
        try:
            from bson import ObjectId
            update_data['updatedAt'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Situation report {report_id} updated successfully")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update situation report: {str(e)}")
            return False
    
    def get_reports_by_dispatch(self, dispatch_id):
        """Get all reports for a specific dispatch."""
        try:
            reports = list(self.collection.find({"dispatchId": dispatch_id}))
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports by dispatch: {str(e)}")
            return []
    
    def get_reports_by_unit(self, unit_id, limit=100):
        """Get reports by response unit."""
        try:
            reports = list(self.collection.find({"unitId": unit_id}).limit(limit))
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports by unit: {str(e)}")
            return []


class Telemetry:
    """MongoDB model for responder unit telemetry."""
    
    def __init__(self, db_manager):
        self.collection = db_manager.get_collection('telemetry')
        self.setup_indexes()
    
    def setup_indexes(self):
        """Setup MongoDB indexes for telemetry."""
        try:
            # TTL index to automatically expire old telemetry data
            self.collection.create_index(
                [("timestamp", ASCENDING)],
                expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
            )
            
            # Index on unit ID for quick lookups
            self.collection.create_index([("unitId", ASCENDING)])
            
            # Index on timestamp for time-based queries
            self.collection.create_index([("timestamp", DESCENDING)])
            
            # 2dsphere index for geospatial queries
            self.collection.create_index([("location", "2dsphere")])
            
            # Compound index for efficient queries
            self.collection.create_index([
                ("unitId", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            logger.info("Telemetry indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create telemetry indexes: {str(e)}")
    
    def create_telemetry(self, telemetry_data):
        """Create a new telemetry record."""
        try:
            # Add timestamp
            telemetry_data['timestamp'] = datetime.utcnow()
            
            # Insert document
            result = self.collection.insert_one(telemetry_data)
            
            logger.debug(f"Telemetry record created with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create telemetry record: {str(e)}")
            raise
    
    def get_unit_telemetry(self, unit_id, hours=24):
        """Get telemetry data for a unit within specified hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            telemetry = list(self.collection.find({
                "unitId": unit_id,
                "timestamp": {"$gte": cutoff_time}
            }).sort("timestamp", DESCENDING))
            
            return telemetry
            
        except Exception as e:
            logger.error(f"Failed to get unit telemetry: {str(e)}")
            return []
    
    def get_location_history(self, unit_id, hours=24):
        """Get location history for a unit."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            locations = list(self.collection.find({
                "unitId": unit_id,
                "timestamp": {"$gte": cutoff_time},
                "location": {"$exists": True}
            }, {
                "location": 1,
                "timestamp": 1,
                "speed": 1,
                "heading": 1
            }).sort("timestamp", ASCENDING))
            
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get location history: {str(e)}")
            return []
    
    def get_units_in_area(self, lat, lon, radius_km=10):
        """Get all units within a radius of a location."""
        try:
            query = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "$maxDistance": radius_km * 1000  # Convert to meters
                    }
                }
            }
            
            # Get latest telemetry for each unit
            pipeline = [
                {"$match": query},
                {"$sort": {"timestamp": DESCENDING}},
                {"$group": {
                    "_id": "$unitId",
                    "latest": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest"}}
            ]
            
            units = list(self.collection.aggregate(pipeline))
            return units
            
        except Exception as e:
            logger.error(f"Failed to get units in area: {str(e)}")
            return []


# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

# Model instances
citizen_reports = CitizenReport(mongodb_manager)
situation_reports = SituationReport(mongodb_manager)
telemetry = Telemetry(mongodb_manager)


def cleanup_old_data():
    """Clean up old data from MongoDB collections."""
    try:
        # Clean up old telemetry data (older than 30 days)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        telemetry_result = telemetry.collection.delete_many({
            "timestamp": {"$lt": cutoff_time}
        })
        
        logger.info(f"Cleaned up {telemetry_result.deleted_count} old telemetry records")
        
        # Clean up old citizen reports (older than 90 days)
        cutoff_time = datetime.utcnow() - timedelta(days=90)
        
        reports_result = citizen_reports.collection.delete_many({
            "reportedAt": {"$lt": cutoff_time},
            "status": {"$in": ["RESOLVED", "CLOSED", "CANCELLED"]}
        })
        
        logger.info(f"Cleaned up {reports_result.deleted_count} old citizen reports")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {str(e)}")


# Example usage functions
def create_sample_citizen_report():
    """Create a sample citizen report for testing."""
    sample_report = {
        "incidentId": 123,
        "reporter": {
            "phone": "+1234567890",
            "appUserId": 42
        },
        "geo": {
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]  # NYC coordinates
        },
        "categoryGuess": "FLOOD",
        "payload": {
            "message": "River burst its banks",
            "tags": ["water", "overflow"],
            "media": [{"url": "https://example.com/image.jpg", "type": "image"}],
            "device": {"platform": "android", "version": "2.3.1"}
        }
    }
    
    return citizen_reports.create_report(sample_report)


def create_sample_situation_report():
    """Create a sample situation report for testing."""
    sample_report = {
        "dispatchId": "dispatch-123",
        "unitId": "unit-456",
        "reporter": {
            "userId": 789,
            "name": "John Doe",
            "role": "Medic"
        },
        "title": "Medical Emergency Response",
        "content": "Patient stabilized and transported to hospital",
        "assessment": "Patient had chest pain, administered treatment",
        "casualties": 1,
        "fatalities": 0,
        "resourcesNeeded": ["additional_medics", "ambulance"],
        "location": {
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        }
    }
    
    return situation_reports.create_report(sample_report)


def create_sample_telemetry():
    """Create a sample telemetry record for testing."""
    sample_telemetry = {
        "unitId": "unit-456",
        "location": {
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        "speed": 45.5,  # km/h
        "heading": 180,  # degrees
        "engineStatus": "running",
        "fuelLevel": 75.2,  # percentage
        "temperature": 22.5,  # celsius
        "sensors": {
            "gps": "active",
            "engine": "normal",
            "communications": "active"
        }
    }
    
    return telemetry.create_telemetry(sample_telemetry)
