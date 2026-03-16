import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Bot, 
  Cpu, 
  Package, 
  AlertTriangle, 
  Zap,
  ArrowRight,
  MessageSquare,
  Activity,
  Clock,
  CheckCircle2
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion, AnimatePresence } from "framer-motion";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Agent configuration
const agentConfig = {
  orchestrator: {
    name: "Orchestrator",
    icon: Cpu,
    color: "#f8fafc",
    bgColor: "rgba(248, 250, 252, 0.1)",
    description: "Coordinates all agents, decomposes tasks, manages workflow execution",
    tools: ["coordinate_agents", "decompose_task", "manage_workflow"],
    responsibilities: ["Task coordination & planning", "Agent selection", "Result aggregation"]
  },
  demand: {
    name: "Demand Agent",
    icon: Activity,
    color: "#a855f7",
    bgColor: "rgba(168, 85, 247, 0.1)",
    description: "Handles demand forecasting, stockout prediction, and anomaly detection",
    tools: ["forecast_product", "get_stockout_risk", "detect_demand_anomaly"],
    responsibilities: ["Demand forecasting", "Stockout prediction", "Demand anomaly detection"]
  },
  inventory: {
    name: "Inventory Agent",
    icon: Package,
    color: "#06b6d4",
    bgColor: "rgba(6, 182, 212, 0.1)",
    description: "Manages reorder points, safety stock, and warehouse balancing",
    tools: ["compute_reorder", "check_warehouse_levels", "calculate_safety_stock"],
    responsibilities: ["Reorder point calculation", "Safety stock optimization", "Warehouse balancing"]
  },
  supplier: {
    name: "Supplier Agent",
    icon: AlertTriangle,
    color: "#f97316",
    bgColor: "rgba(249, 115, 22, 0.1)",
    description: "Monitors supplier risks, optimizes shipping, and tracks vendors",
    tools: ["score_supplier_risk", "get_best_shipping_mode", "flag_vendor"],
    responsibilities: ["Supplier risk scoring", "Shipping mode optimization", "Vendor monitoring"]
  },
  action: {
    name: "Action Agent",
    icon: Zap,
    color: "#3b82f6",
    bgColor: "rgba(59, 130, 246, 0.1)",
    description: "Executes purchase orders, sends alerts, and generates reports",
    tools: ["raise_purchase_order", "generate_po_pdf", "send_alert", "log_decision"],
    responsibilities: ["Raise purchase orders", "Send alerts", "Generate reports", "Log decisions"]
  },
};

// Status indicator component
const StatusIndicator = ({ status }) => {
  const statusStyles = {
    idle: { color: "#71717a", label: "Idle" },
    thinking: { color: "#f59e0b", label: "Thinking" },
    acting: { color: "#10b981", label: "Acting" },
    waiting: { color: "#6366f1", label: "Waiting" },
  };

  const style = statusStyles[status] || statusStyles.idle;

  return (
    <div className="flex items-center gap-2">
      <div 
        className={`w-2 h-2 rounded-full ${status !== 'idle' ? 'animate-pulse' : ''}`}
        style={{ backgroundColor: style.color }}
      />
      <span className="text-xs text-zinc-400">{style.label}</span>
    </div>
  );
};

// Agent Node Component
const AgentNode = ({ agentKey, state, isSelected, onClick }) => {
  const config = agentConfig[agentKey];
  const Icon = config.icon;
  const status = state?.status || "idle";
  const isActive = status !== "idle";

  return (
    <motion.div
      className={`relative p-4 rounded-xl border cursor-pointer transition-all duration-300 ${
        isSelected 
          ? 'border-white/20 bg-zinc-800/50' 
          : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700'
      }`}
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      data-testid={`agent-node-${agentKey}`}
    >
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-xl"
          style={{ 
            boxShadow: `0 0 20px ${config.color}40`,
            border: `1px solid ${config.color}40`
          }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      )}
      
      <div className="flex items-center gap-3 mb-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: config.bgColor }}
        >
          <Icon className="w-5 h-5" style={{ color: config.color }} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">{config.name}</h3>
          <StatusIndicator status={status} />
        </div>
      </div>

      {state?.current_task && (
        <div className="text-xs text-zinc-500 bg-zinc-900 rounded px-2 py-1 truncate">
          {state.current_task}
        </div>
      )}
    </motion.div>
  );
};

// Message Bus Visualizer
const MessageBusVisualizer = ({ messages }) => {
  return (
    <div className="space-y-3" data-testid="message-bus">
      <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
        Message Bus
      </h3>
      
      <ScrollArea className="h-64 rounded-lg border border-zinc-800 bg-zinc-900/30">
        <div className="p-3 space-y-2">
          {messages.length === 0 ? (
            <div className="text-center text-zinc-600 py-8">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No messages yet</p>
            </div>
          ) : (
            messages.map((msg, idx) => {
              const fromConfig = agentConfig[msg.from_agent];
              const toConfig = agentConfig[msg.to_agent];
              
              return (
                <div 
                  key={msg.id || idx}
                  className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded-lg text-xs"
                >
                  <div 
                    className="w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: fromConfig?.bgColor || '#27272a' }}
                  >
                    {fromConfig && <fromConfig.icon className="w-3 h-3" style={{ color: fromConfig.color }} />}
                  </div>
                  <ArrowRight className="w-3 h-3 text-zinc-600" />
                  <div 
                    className="w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: toConfig?.bgColor || '#27272a' }}
                  >
                    {toConfig && <toConfig.icon className="w-3 h-3" style={{ color: toConfig.color }} />}
                  </div>
                  <span className="text-zinc-400 flex-1 truncate">{msg.message_type}</span>
                  <span className="text-zinc-600">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

// Agent Detail Panel
const AgentDetailPanel = ({ agentKey }) => {
  if (!agentKey) return null;
  
  const config = agentConfig[agentKey];
  const Icon = config.icon;

  return (
    <div className="space-y-6" data-testid="agent-detail">
      <div className="flex items-start gap-4">
        <div 
          className="w-14 h-14 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: config.bgColor }}
        >
          <Icon className="w-7 h-7" style={{ color: config.color }} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">{config.name}</h2>
          <p className="text-sm text-zinc-400 mt-1">{config.description}</p>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Responsibilities
        </h3>
        <div className="space-y-2">
          {config.responsibilities.map((resp, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm text-zinc-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              {resp}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Available Tools
        </h3>
        <div className="flex flex-wrap gap-2">
          {config.tools.map((tool, idx) => (
            <Badge 
              key={idx}
              variant="outline"
              className="font-mono text-xs"
              style={{ borderColor: config.color, color: config.color }}
            >
              {tool}()
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
};

export default function Agents({ agentStates }) {
  const [messages, setMessages] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("orchestrator");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await axios.get(`${API}/agents/messages`);
        setMessages(response.data.messages);
      } catch (error) {
        console.error("Failed to fetch messages:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6" data-testid="agents-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Multi-Agent System</h1>
        <p className="text-zinc-500 mt-1">Real-time view of AI agents orchestrating supply chain operations</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Agent Grid */}
        <div className="col-span-8 space-y-6">
          {/* Agent Network Visualization */}
          <div className="p-6 bg-zinc-900/30 rounded-xl border border-zinc-800/50">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
              Agent Network
            </h3>
            
            {/* Orchestrator at top */}
            <div className="flex justify-center mb-4">
              <div className="w-64">
                <AgentNode
                  agentKey="orchestrator"
                  state={agentStates?.orchestrator}
                  isSelected={selectedAgent === "orchestrator"}
                  onClick={() => setSelectedAgent("orchestrator")}
                />
              </div>
            </div>

            {/* Connection lines */}
            <div className="flex justify-center mb-4">
              <div className="w-px h-8 bg-gradient-to-b from-zinc-600 to-transparent" />
            </div>

            {/* Other agents in a row */}
            <div className="grid grid-cols-4 gap-4">
              {["demand", "inventory", "supplier", "action"].map((agentKey) => (
                <AgentNode
                  key={agentKey}
                  agentKey={agentKey}
                  state={agentStates?.[agentKey]}
                  isSelected={selectedAgent === agentKey}
                  onClick={() => setSelectedAgent(agentKey)}
                />
              ))}
            </div>
          </div>

          {/* Message Bus */}
          <div className="p-6 bg-zinc-900/30 rounded-xl border border-zinc-800/50">
            <MessageBusVisualizer messages={messages} />
          </div>
        </div>

        {/* Agent Detail Panel */}
        <div className="col-span-4">
          <div className="p-6 bg-zinc-900/30 rounded-xl border border-zinc-800/50 sticky top-24">
            <AgentDetailPanel agentKey={selectedAgent} />
          </div>
        </div>
      </div>
    </div>
  );
}
