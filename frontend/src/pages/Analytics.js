import { useState, useEffect } from "react";
import axios from "axios";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Truck, 
  Package,
  BarChart3,
  PieChart as PieIcon,
  Activity
} from "lucide-react";
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Custom tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="value" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const COLORS = ['#6366f1', '#06b6d4', '#f97316', '#22c55e', '#a855f7'];

export default function Analytics() {
  const [demandTrend, setDemandTrend] = useState([]);
  const [inventoryLevels, setInventoryLevels] = useState([]);
  const [supplierPerformance, setSupplierPerformance] = useState([]);
  const [costBreakdown, setCostBreakdown] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        const [demandRes, inventoryRes, supplierRes, costRes] = await Promise.all([
          axios.get(`${API}/analytics/demand-trend`),
          axios.get(`${API}/analytics/inventory-levels`),
          axios.get(`${API}/analytics/supplier-performance`),
          axios.get(`${API}/analytics/cost-breakdown`),
        ]);
        
        setDemandTrend(demandRes.data.data);
        setInventoryLevels(inventoryRes.data.data);
        setSupplierPerformance(supplierRes.data.data);
        setCostBreakdown(costRes.data.data);
      } catch (error) {
        console.error("Failed to fetch analytics data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="analytics-loading">
        <div className="text-zinc-500">Loading analytics...</div>
      </div>
    );
  }

  // Transform supplier data for radar chart
  const radarData = supplierPerformance.length > 0 ? [
    { metric: 'Quality', value: supplierPerformance.reduce((a, b) => a + b.quality, 0) / supplierPerformance.length },
    { metric: 'Delivery', value: supplierPerformance.reduce((a, b) => a + b.delivery, 0) / supplierPerformance.length },
    { metric: 'Cost', value: supplierPerformance.reduce((a, b) => a + b.cost, 0) / supplierPerformance.length },
    { metric: 'Risk (inv)', value: 100 - supplierPerformance.reduce((a, b) => a + b.risk, 0) / supplierPerformance.length },
  ] : [];

  return (
    <div className="space-y-6" data-testid="analytics-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
        <p className="text-zinc-500 mt-1">Deep insights into supply chain performance</p>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="suppliers">Suppliers</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="roi">ROI Analysis</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="bento-grid">
            {/* Demand Trend */}
            <div className="bento-item span-8" data-testid="demand-trend-chart">
              <h3 className="text-lg font-semibold text-white mb-4">Demand Trend Analysis</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={demandTrend}>
                    <defs>
                      <linearGradient id="colorActual2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
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
                      fill="url(#colorActual2)"
                      strokeWidth={2}
                      name="Actual Demand"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="forecast" 
                      stroke="#06b6d4" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      name="Forecast"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Inventory Health */}
            <div className="bento-item span-4" data-testid="inventory-health-chart">
              <h3 className="text-lg font-semibold text-white mb-4">Inventory by Warehouse</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={inventoryLevels}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="warehouse" stroke="#71717a" fontSize={12} />
                    <YAxis stroke="#71717a" fontSize={12} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="current" fill="#6366f1" radius={[4, 4, 0, 0]} name="Current" />
                    <Bar dataKey="optimal" fill="#3f3f46" radius={[4, 4, 0, 0]} name="Optimal" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Suppliers Tab */}
        <TabsContent value="suppliers" className="space-y-6 mt-6">
          <div className="grid grid-cols-12 gap-6">
            {/* Supplier Performance Table */}
            <div className="col-span-8 bg-zinc-900/50 rounded-xl border border-zinc-800/50 p-6" data-testid="supplier-table">
              <h3 className="text-lg font-semibold text-white mb-4">Supplier Performance Matrix</h3>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Supplier</th>
                    <th>Quality</th>
                    <th>Delivery</th>
                    <th>Cost</th>
                    <th>Risk Score</th>
                  </tr>
                </thead>
                <tbody>
                  {supplierPerformance.map((supplier, idx) => (
                    <tr key={idx}>
                      <td className="font-medium text-white">{supplier.supplier}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500 rounded-full" 
                              style={{ width: `${supplier.quality}%` }}
                            />
                          </div>
                          <span className="text-xs">{supplier.quality}%</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500 rounded-full" 
                              style={{ width: `${supplier.delivery}%` }}
                            />
                          </div>
                          <span className="text-xs">{supplier.delivery}%</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-amber-500 rounded-full" 
                              style={{ width: `${supplier.cost}%` }}
                            />
                          </div>
                          <span className="text-xs">{supplier.cost}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`risk-badge ${supplier.risk < 30 ? 'low' : supplier.risk < 50 ? 'medium' : 'high'}`}>
                          {supplier.risk}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Radar Chart */}
            <div className="col-span-4 bg-zinc-900/50 rounded-xl border border-zinc-800/50 p-6" data-testid="supplier-radar">
              <h3 className="text-lg font-semibold text-white mb-4">Average Performance</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#3f3f46" />
                    <PolarAngleAxis dataKey="metric" stroke="#71717a" fontSize={12} />
                    <PolarRadiusAxis stroke="#3f3f46" fontSize={10} />
                    <Radar 
                      name="Average" 
                      dataKey="value" 
                      stroke="#6366f1" 
                      fill="#6366f1" 
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Costs Tab */}
        <TabsContent value="costs" className="space-y-6 mt-6">
          <div className="grid grid-cols-12 gap-6">
            {/* Cost Breakdown Pie Chart */}
            <div className="col-span-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50 p-6" data-testid="cost-pie-chart">
              <h3 className="text-lg font-semibold text-white mb-4">Logistics Cost Breakdown</h3>
              <div className="h-72 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={costBreakdown}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {costBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {costBreakdown.map((entry, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                    <span className="text-xs text-zinc-400">{entry.category}: {entry.value}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Cost Trends */}
            <div className="col-span-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50 p-6" data-testid="cost-trends">
              <h3 className="text-lg font-semibold text-white mb-4">Cost Optimization Trends</h3>
              <div className="space-y-4">
                {costBreakdown.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                      <span className="text-sm text-zinc-300">{item.category}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono text-white">{item.value}%</span>
                      <div className={`flex items-center gap-1 text-xs ${item.trend < 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {item.trend < 0 ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                        {Math.abs(item.trend)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ROI Tab */}
        <TabsContent value="roi" className="space-y-6 mt-6">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-8 bg-zinc-900/50 rounded-xl border border-zinc-800/50 p-6" data-testid="roi-analysis">
              <h3 className="text-lg font-semibold text-white mb-6">ROI Analysis - Mid-Size Enterprise ($500M Revenue)</h3>
              
              <div className="space-y-6">
                {/* Direct Cost Savings */}
                <div>
                  <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Direct Cost Savings</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { label: "Inventory Reduction", value: "$2.5M", desc: "15% reduction in carrying costs" },
                      { label: "Logistics Optimization", value: "$1.8M", desc: "12% transportation savings" },
                      { label: "Procurement Efficiency", value: "$800K", desc: "Reduced maverick spending" },
                    ].map((item, idx) => (
                      <div key={idx} className="p-4 bg-zinc-800/30 rounded-lg">
                        <p className="text-xs text-zinc-500 mb-1">{item.label}</p>
                        <p className="text-2xl font-bold text-emerald-400 font-mono">{item.value}</p>
                        <p className="text-xs text-zinc-500 mt-1">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Operational Improvements */}
                <div>
                  <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Operational Improvements</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { label: "Disruption Response", value: "40%", desc: "Faster response time" },
                      { label: "Forecast Accuracy", value: "25%", desc: "Improvement" },
                      { label: "Manual Effort", value: "60%", desc: "Reduction" },
                    ].map((item, idx) => (
                      <div key={idx} className="p-4 bg-zinc-800/30 rounded-lg">
                        <p className="text-xs text-zinc-500 mb-1">{item.label}</p>
                        <p className="text-2xl font-bold text-blue-400 font-mono">{item.value}</p>
                        <p className="text-xs text-zinc-500 mt-1">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* ROI Summary */}
            <div className="col-span-4 space-y-4">
              {[
                { label: "Total Annual Benefit", value: "$5.1M", color: "#10b981" },
                { label: "Implementation Cost", value: "$1.2M", color: "#f97316" },
                { label: "Payback Period", value: "2.8 months", color: "#6366f1" },
                { label: "3-Year ROI", value: "425%", color: "#a855f7" },
              ].map((item, idx) => (
                <div key={idx} className="p-5 bg-zinc-900/50 rounded-xl border border-zinc-800/50">
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">{item.label}</p>
                  <p className="text-3xl font-bold font-mono mt-2" style={{ color: item.color }}>{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
