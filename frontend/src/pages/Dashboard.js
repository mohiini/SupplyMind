import { useState, useEffect } from "react";
import axios from "axios";
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  Truck, 
  AlertTriangle,
  DollarSign,
  BarChart3,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Bot
} from "lucide-react";
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell
} from "recharts";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="value" style={{ color: entry.color }}>
            {entry.name}: {entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// KPI Card Component
const KPICard = ({ label, value, change, trend, icon: Icon, color }) => (
  <div className="kpi-card" style={{ '--accent-color': color }} data-testid={`kpi-${label.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="flex justify-between items-start">
      <div>
        <p className="kpi-label">{label}</p>
        <p className="kpi-value">{value}</p>
        <div className={`kpi-change ${trend === 'up' ? 'positive' : 'negative'}`}>
          {trend === 'up' ? (
            <ArrowUpRight className="w-4 h-4" />
          ) : (
            <ArrowDownRight className="w-4 h-4" />
          )}
          <span>{Math.abs(change)}% vs last period</span>
        </div>
      </div>
      <div 
        className="w-10 h-10 rounded-lg flex items-center justify-center"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
    </div>
  </div>
);

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [kpis, setKpis] = useState([]);
  const [demandTrend, setDemandTrend] = useState([]);
  const [inventoryLevels, setInventoryLevels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [metricsRes, kpisRes, demandRes, inventoryRes] = await Promise.all([
          axios.get(`${API}/metrics/system`),
          axios.get(`${API}/metrics/kpis`),
          axios.get(`${API}/analytics/demand-trend`),
          axios.get(`${API}/analytics/inventory-levels`),
        ]);
        
        setMetrics(metricsRes.data);
        setKpis(kpisRes.data.kpis);
        setDemandTrend(demandRes.data.data);
        setInventoryLevels(inventoryRes.data.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const kpiIcons = {
    "Cost Savings": DollarSign,
    "On-Time Delivery": Truck,
    "Inventory Turnover": Package,
    "Supplier Risk Score": AlertTriangle,
    "Forecast Accuracy": BarChart3,
    "Carbon Footprint": Activity,
  };

  const kpiColors = {
    "Cost Savings": "#10b981",
    "On-Time Delivery": "#3b82f6",
    "Inventory Turnover": "#f59e0b",
    "Supplier Risk Score": "#f97316",
    "Forecast Accuracy": "#6366f1",
    "Carbon Footprint": "#22c55e",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="dashboard-loading">
        <div className="text-zinc-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
          <p className="text-zinc-500 mt-1">Supply chain intelligence overview</p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 bg-zinc-900 rounded-lg border border-zinc-800">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-sm text-zinc-400">System Active</span>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="kpi-grid">
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.name}
            label={kpi.name}
            value={kpi.value}
            change={kpi.change}
            trend={kpi.trend}
            icon={kpiIcons[kpi.name] || Activity}
            color={kpiColors[kpi.name] || "#6366f1"}
          />
        ))}
      </div>

      {/* Charts Grid */}
      <div className="bento-grid">
        {/* Demand Trend Chart */}
        <div className="bento-item span-8" data-testid="demand-chart">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">Demand Trend</h3>
            <span className="text-xs text-zinc-500">Actual vs Forecast</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={demandTrend}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="month" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#6366f1" 
                  fillOpacity={1} 
                  fill="url(#colorActual)"
                  strokeWidth={2}
                  name="Actual"
                />
                <Area 
                  type="monotone" 
                  dataKey="forecast" 
                  stroke="#06b6d4" 
                  fillOpacity={1} 
                  fill="url(#colorForecast)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Forecast"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* System Status */}
        <div className="bento-item span-4" data-testid="system-status">
          <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-indigo-400" />
                </div>
                <span className="text-sm text-zinc-300">Active Agents</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{metrics?.active_agents || 5}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-purple-400" />
                </div>
                <span className="text-sm text-zinc-300">Workflows</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{metrics?.total_workflows || 10}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-emerald-400" />
                </div>
                <span className="text-sm text-zinc-300">Decisions Today</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{metrics?.decisions_today || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                </div>
                <span className="text-sm text-zinc-300">Risk Alerts</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{metrics?.risk_alerts || 0}</span>
            </div>
          </div>
        </div>

        {/* Inventory Levels */}
        <div className="bento-item span-6" data-testid="inventory-chart">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">Inventory by Warehouse</h3>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={inventoryLevels} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" stroke="#71717a" fontSize={12} />
                <YAxis dataKey="warehouse" type="category" stroke="#71717a" fontSize={12} width={60} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="current" fill="#6366f1" radius={[0, 4, 4, 0]} name="Current" />
                <Bar dataKey="optimal" fill="#3f3f46" radius={[0, 4, 4, 0]} name="Optimal" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bento-item span-6" data-testid="quick-actions">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Run Forecast", icon: TrendingUp, color: "#6366f1" },
              { label: "Check Inventory", icon: Package, color: "#06b6d4" },
              { label: "Analyze Suppliers", icon: AlertTriangle, color: "#f97316" },
              { label: "Generate Report", icon: BarChart3, color: "#22c55e" },
            ].map((action) => (
              <button
                key={action.label}
                className="flex items-center gap-3 p-4 bg-zinc-900/50 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors text-left"
                data-testid={`action-${action.label.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${action.color}20` }}
                >
                  <action.icon className="w-5 h-5" style={{ color: action.color }} />
                </div>
                <span className="text-sm font-medium text-zinc-300">{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
