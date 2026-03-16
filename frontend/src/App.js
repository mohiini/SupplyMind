import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  LayoutDashboard, 
  Workflow, 
  Bot, 
  BarChart3, 
  FileText, 
  AlertTriangle,
  Package,
  TrendingUp,
  Activity,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  Zap
} from "lucide-react";

// Pages
import Dashboard from "./pages/Dashboard";
import Workflows from "./pages/Workflows";
import Agents from "./pages/Agents";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import SupplierRiskDemo from "./pages/SupplierRiskDemo";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Sidebar Navigation
const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const navItems = [
    { path: "/", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/workflows", icon: Workflow, label: "Workflows" },
    { path: "/agents", icon: Bot, label: "Agents" },
    { path: "/analytics", icon: BarChart3, label: "Analytics" },
    { path: "/reports", icon: FileText, label: "Reports" },
    { path: "/supplier-risk", icon: AlertTriangle, label: "Supplier Risk Demo" },
  ];

  return (
    <aside className="sidebar" data-testid="sidebar">
      <div className="sidebar-header">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">SupplyMind</h1>
            <p className="text-xs text-zinc-500">Agentic AI OS</p>
          </div>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <div
            key={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
            data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <item.icon className="w-5 h-5 nav-icon" />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
      
      <div className="p-4 border-t border-zinc-800/50">
        <div className="text-xs text-zinc-600 mb-1">Version 1.0.0</div>
        <div className="text-xs text-zinc-500">Powered by Ollama Llama3</div>
      </div>
    </aside>
  );
};

// Agent Status Bar
const AgentStatusBar = ({ agentStates }) => {
  const agents = [
    { key: "orchestrator", label: "Orchestrator", color: "#f8fafc" },
    { key: "demand", label: "Demand", color: "#a855f7" },
    { key: "inventory", label: "Inventory", color: "#06b6d4" },
    { key: "supplier", label: "Supplier", color: "#f97316" },
    { key: "action", label: "Action", color: "#3b82f6" },
  ];

  return (
    <div className="agent-status-bar" data-testid="agent-status-bar">
      <div className="flex items-center gap-2 text-zinc-400 text-sm">
        <Activity className="w-4 h-4" />
        <span>Agent Status:</span>
      </div>
      
      {agents.map((agent) => {
        const state = agentStates?.[agent.key];
        const status = state?.status || "idle";
        
        return (
          <div 
            key={agent.key} 
            className="agent-indicator"
            data-testid={`agent-indicator-${agent.key}`}
          >
            <div 
              className={`agent-dot ${status}`}
              style={{ backgroundColor: status !== "idle" ? agent.color : undefined }}
            />
            <span className="text-xs text-zinc-400">{agent.label}</span>
            <span className="text-xs text-zinc-600 capitalize">{status}</span>
          </div>
        );
      })}
    </div>
  );
};

// Main App Layout
const AppLayout = ({ children, agentStates }) => {
  return (
    <div className="app-container">
      <Sidebar />
      <AgentStatusBar agentStates={agentStates} />
      <main className="main-content" style={{ paddingTop: '80px' }}>
        {children}
      </main>
    </div>
  );
};

function App() {
  const [agentStates, setAgentStates] = useState({});
  const [loading, setLoading] = useState(true);

  // Fetch agent states periodically
  const fetchAgentStates = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/agents/states`);
      setAgentStates(response.data.agents);
    } catch (error) {
      console.error("Failed to fetch agent states:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgentStates();
    const interval = setInterval(fetchAgentStates, 5000);
    return () => clearInterval(interval);
  }, [fetchAgentStates]);

  return (
    <BrowserRouter>
      <Toaster 
        position="top-right" 
        theme="dark"
        toastOptions={{
          style: {
            background: 'rgba(24, 24, 27, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#f4f4f5',
          },
        }}
      />
      <AppLayout agentStates={agentStates}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/agents" element={<Agents agentStates={agentStates} />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/supplier-risk" element={<SupplierRiskDemo />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default App;
