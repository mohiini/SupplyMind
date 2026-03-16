import { useState, useEffect } from "react";
import axios from "axios";
import { 
  TrendingUp, 
  Package, 
  Warehouse, 
  Route, 
  Clock,
  AlertTriangle,
  ShoppingCart,
  DollarSign,
  Factory,
  Leaf,
  ChevronRight,
  Bot,
  Check
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const workflowIcons = {
  "Demand Forecasting": TrendingUp,
  "Inventory Optimization": Package,
  "Warehouse Automation": Warehouse,
  "Route Optimization": Route,
  "Shipment Delay Prediction": Clock,
  "Supplier Risk Detection": AlertTriangle,
  "Procurement Automation": ShoppingCart,
  "Logistics Cost Optimization": DollarSign,
  "Production Planning": Factory,
  "Sustainability Tracking": Leaf,
};

const categoryColors = {
  customer: "#a855f7",
  operations: "#3b82f6",
  infrastructure: "#06b6d4",
  business: "#f97316",
  sustainability: "#22c55e",
};

const typeLabels = {
  execution: "Execution",
  efficiency: "Efficiency",
  exception: "Exception",
  expansion: "Expansion",
};

// Workflow Card Component
const WorkflowCard = ({ workflow, isSelected, onClick }) => {
  const Icon = workflowIcons[workflow.name] || Package;
  const categoryColor = categoryColors[workflow.category] || "#6366f1";
  
  return (
    <div 
      className={`workflow-card ${isSelected ? 'active' : ''}`}
      onClick={onClick}
      data-testid={`workflow-card-${workflow.id}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${categoryColor}15` }}
        >
          <Icon className="w-5 h-5" style={{ color: categoryColor }} />
        </div>
        <Badge 
          variant="outline" 
          className="text-xs capitalize"
          style={{ borderColor: categoryColor, color: categoryColor }}
        >
          {workflow.category}
        </Badge>
      </div>
      
      <h3 className="text-base font-semibold text-white mb-1">{workflow.name}</h3>
      <p className="text-sm text-zinc-500 mb-3 line-clamp-2">{workflow.description}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          {workflow.agents_involved.map((agent, idx) => (
            <div 
              key={idx}
              className="w-6 h-6 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center"
              title={agent}
            >
              <Bot className="w-3 h-3 text-zinc-400" />
            </div>
          ))}
        </div>
        <span className="text-xs text-zinc-600 capitalize">{typeLabels[workflow.workflow_type]}</span>
      </div>
    </div>
  );
};

// Workflow Detail Panel
const WorkflowDetail = ({ workflow }) => {
  if (!workflow) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500">
        Select a workflow to view details
      </div>
    );
  }

  const Icon = workflowIcons[workflow.name] || Package;
  const categoryColor = categoryColors[workflow.category] || "#6366f1";
  
  const deepDiveContent = {
    "Demand Forecasting": {
      baseline: "Manual forecasting using spreadsheets and historical averages",
      staticData: "Historical sales data, product catalog, pricing information",
      dynamicData: "Real-time POS data, market trends, promotional calendars",
      features: "Seasonality indices, trend components, external factors (weather, events)",
      models: "ARIMA, Prophet, LSTM neural networks, Gradient Boosting",
      llmRole: "Interpret forecast results, explain anomalies, suggest actions",
      metrics: "MAPE, WMAPE, Forecast Bias, Forecast Value Added (FVA)",
    },
    "Inventory Optimization": {
      baseline: "Fixed reorder points based on supplier lead times",
      staticData: "SKU master data, warehouse locations, storage costs",
      dynamicData: "Real-time inventory levels, demand signals, supplier status",
      features: "Service level targets, ABC classification, lead time variability",
      models: "Economic Order Quantity, Safety Stock models, Multi-echelon optimization",
      llmRole: "Explain optimization decisions, handle exceptions, suggest alternatives",
      metrics: "Fill Rate, Inventory Turnover, Carrying Cost, Stockout Rate",
    },
    "Route Optimization": {
      baseline: "Static routing based on geography and driver assignments",
      staticData: "Road networks, vehicle fleet data, customer locations",
      dynamicData: "Traffic conditions, weather, delivery windows, capacity",
      features: "Distance matrices, time windows, vehicle constraints, priorities",
      models: "Vehicle Routing Problem (VRP) solvers, Genetic Algorithms, OR-Tools",
      llmRole: "Handle exceptions, communicate delays, suggest re-routing",
      metrics: "Miles Driven, On-Time Delivery, Cost per Delivery, Utilization",
    },
    "Shipment Delay Prediction": {
      baseline: "Reactive delay management after issues occur",
      staticData: "Carrier performance history, lane statistics, port data",
      dynamicData: "GPS tracking, weather forecasts, port congestion, customs status",
      features: "Transit time features, carrier reliability scores, external risk factors",
      models: "Random Forest, XGBoost, Neural Networks for time series",
      llmRole: "Explain predictions, suggest mitigation, draft communications",
      metrics: "Prediction Accuracy, Lead Time, False Positive Rate, Recovery Rate",
    },
    "Supplier Risk Detection": {
      baseline: "Annual supplier reviews and manual monitoring",
      staticData: "Supplier profiles, financial data, certification records",
      dynamicData: "News feeds, social media, market data, performance metrics",
      features: "Financial ratios, sentiment scores, compliance indicators",
      models: "NLP for sentiment analysis, anomaly detection, risk scoring models",
      llmRole: "Analyze news, summarize risks, recommend actions, draft alerts",
      metrics: "Risk Score Accuracy, Early Warning Rate, Supplier Retention",
    },
  };

  const details = deepDiveContent[workflow.name] || {};

  return (
    <div className="space-y-6" data-testid="workflow-detail">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div 
          className="w-14 h-14 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: `${categoryColor}15` }}
        >
          <Icon className="w-7 h-7" style={{ color: categoryColor }} />
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-white">{workflow.name}</h2>
          <p className="text-zinc-400 mt-1">{workflow.description}</p>
          <div className="flex gap-2 mt-3">
            <Badge style={{ backgroundColor: `${categoryColor}20`, color: categoryColor }}>
              {workflow.category}
            </Badge>
            <Badge variant="outline">{typeLabels[workflow.workflow_type]}</Badge>
          </div>
        </div>
      </div>

      {/* Metrics */}
      {workflow.metrics && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(workflow.metrics).map(([key, value]) => (
            <div key={key} className="p-4 bg-zinc-900/50 rounded-lg">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">
                {key.replace(/_/g, ' ')}
              </p>
              <p className="text-xl font-mono font-bold text-white">
                {typeof value === 'number' && value < 1 ? `${(value * 100).toFixed(1)}%` : value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Agents Involved */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Agents Involved
        </h3>
        <div className="flex flex-wrap gap-2">
          {workflow.agents_involved.map((agent, idx) => (
            <div 
              key={idx}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-agent-${agent} border border-zinc-800`}
            >
              <Bot className={`w-4 h-4 agent-${agent}`} />
              <span className="text-sm text-zinc-300 capitalize">{agent}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Deep Dive (for specific workflows) */}
      {Object.keys(details).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
            Technical Deep Dive
          </h3>
          
          <div className="grid gap-3">
            {Object.entries(details).map(([key, value]) => (
              <div key={key} className="p-3 bg-zinc-900/30 rounded-lg border border-zinc-800/50">
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </p>
                <p className="text-sm text-zinc-300">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await axios.get(`${API}/workflows`);
        setWorkflows(response.data.workflows);
        if (response.data.workflows.length > 0) {
          setSelectedWorkflow(response.data.workflows[0]);
        }
      } catch (error) {
        console.error("Failed to fetch workflows:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="workflows-loading">
        <div className="text-zinc-500">Loading workflows...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="workflows-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Workflows</h1>
        <p className="text-zinc-500 mt-1">10 supply chain workflows powered by multi-agent AI</p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-6">
        {/* Workflow List */}
        <div className="col-span-5 space-y-3" data-testid="workflow-list">
          {workflows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow}
              isSelected={selectedWorkflow?.id === workflow.id}
              onClick={() => setSelectedWorkflow(workflow)}
            />
          ))}
        </div>

        {/* Workflow Detail */}
        <div className="col-span-7 bg-zinc-900/30 rounded-xl border border-zinc-800/50 p-6">
          <WorkflowDetail workflow={selectedWorkflow} />
        </div>
      </div>
    </div>
  );
}
