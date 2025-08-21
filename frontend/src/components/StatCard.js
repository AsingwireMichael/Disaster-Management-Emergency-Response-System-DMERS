import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  AlertTriangle,
  Users,
  Clock,
  MapPin,
  Activity
} from 'lucide-react';

const StatCard = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon: Icon, 
  color = 'blue',
  subtitle 
}) => {
  const getChangeIcon = () => {
    if (changeType === 'positive') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (changeType === 'negative') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  const getChangeColor = () => {
    if (changeType === 'positive') return 'text-green-600';
    if (changeType === 'negative') return 'text-red-600';
    return 'text-gray-600';
  };

  const getIconColor = () => {
    const colors = {
      blue: 'text-blue-500 bg-blue-100',
      green: 'text-green-500 bg-green-100',
      red: 'text-red-500 bg-red-100',
      yellow: 'text-yellow-500 bg-yellow-100',
      purple: 'text-purple-500 bg-purple-100',
      orange: 'text-orange-500 bg-orange-100'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {Icon && (
              <div className={`p-2 rounded-lg ${getIconColor()}`}>
                <Icon className="w-5 h-5" />
              </div>
            )}
            <p className="text-sm font-medium text-gray-600">{title}</p>
          </div>
          
          <div className="flex items-baseline space-x-2">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {change && (
              <div className={`flex items-center space-x-1 text-sm ${getChangeColor()}`}>
                {getChangeIcon()}
                <span>{change}</span>
              </div>
            )}
          </div>
          
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Predefined stat card variants
export const IncidentStatCard = ({ value, change, changeType }) => (
  <StatCard
    title="Active Incidents"
    value={value}
    change={change}
    changeType={changeType}
    icon={AlertTriangle}
    color="red"
    subtitle="Currently being handled"
  />
);

export const UnitStatCard = ({ value, change, changeType }) => (
  <StatCard
    title="Available Units"
    value={value}
    change={change}
    changeType={changeType}
    icon={Users}
    color="green"
    subtitle="Ready for dispatch"
  />
);

export const ResponseTimeStatCard = ({ value, change, changeType }) => (
  <StatCard
    title="Avg Response Time"
    value={value}
    change={change}
    changeType={changeType}
    icon={Clock}
    color="blue"
    subtitle="Minutes to arrival"
  />
);

export const ShelterStatCard = ({ value, change, changeType }) => (
  <StatCard
    title="Shelter Capacity"
    value={value}
    change={change}
    changeType={changeType}
    icon={MapPin}
    color="purple"
    subtitle="Available spaces"
  />
);

export const PerformanceStatCard = ({ value, change, changeType }) => (
  <StatCard
    title="System Performance"
    value={value}
    change={change}
    changeType={changeType}
    icon={Activity}
    color="orange"
    subtitle="Overall efficiency"
  />
);

export default StatCard;
