import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Users, 
  Building2, 
  Clock, 
  MapPin, 
  TrendingUp,
  Activity
} from 'lucide-react';
import axios from 'axios';
import IncidentMap from '../components/IncidentMap';
import StatCard from '../components/StatCard';
import RecentIncidents from '../components/RecentIncidents';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsResponse, incidentsResponse] = await Promise.all([
        axios.get('/api/incidents/statistics/'),
        axios.get('/api/incidents/')
      ]);

      setStats(statsResponse.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of emergency response operations
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Incidents"
          value={stats?.active_incidents || 0}
          icon={AlertTriangle}
          color="emergency"
          change={stats?.today || 0}
          changeLabel="Today"
        />
        <StatCard
          title="Available Units"
          value={stats?.available_units || 0}
          icon={Users}
          color="success"
          change={stats?.total_units || 0}
          changeLabel="Total"
        />
        <StatCard
          title="Shelter Capacity"
          value={stats?.shelter_occupancy || 0}
          icon={Building2}
          color="warning"
          change={stats?.total_shelters || 0}
          changeLabel="Shelters"
        />
        <StatCard
          title="Avg Response Time"
          value={`${Math.round((stats?.avg_response_time_seconds || 0) / 60)}m`}
          icon={Clock}
          color="primary"
          change={stats?.total_incidents || 0}
          changeLabel="Total Incidents"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Incident Map */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Live Incident Map</h3>
            <p className="mt-1 text-sm text-gray-500">
              Real-time location of active incidents
            </p>
          </div>
          <div className="p-6">
            <IncidentMap />
          </div>
        </div>

        {/* Recent Incidents */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Incidents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Latest emergency reports
            </p>
          </div>
          <div className="p-6">
            <RecentIncidents />
          </div>
        </div>
      </div>

      {/* Additional metrics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Incident Categories */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Incident Categories</h3>
          </div>
          <div className="p-6">
            {stats?.by_category && (
              <div className="space-y-3">
                {stats.by_category.map((category) => (
                  <div key={category.category} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">
                      {category.category}
                    </span>
                    <span className="text-sm text-gray-900">{category.count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Regional Overview */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Regional Overview</h3>
          </div>
          <div className="p-6">
            {stats?.by_region && (
              <div className="space-y-3">
                {stats.by_region.slice(0, 5).map((region) => (
                  <div key={region.region} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">
                      {region.region}
                    </span>
                    <span className="text-sm text-gray-900">{region.incidents}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Report Incident
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <Users className="h-4 w-4 mr-2" />
                Dispatch Unit
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <Building2 className="h-4 w-4 mr-2" />
                Check Shelters
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
