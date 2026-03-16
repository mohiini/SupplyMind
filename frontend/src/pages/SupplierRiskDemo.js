import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  AlertTriangle, 
  Search, 
  Loader2, 
  CheckCircle2,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Bot,
  Zap,
  Clock,
  FileText,
  ArrowRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion, AnimatePresence } from "framer-motion";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Sample suppliers for quick selection
const sampleSuppliers = [
  "Acme Manufacturing",
  "Global Parts Inc",
  "FastShip Logistics",
  "MegaSupply Co",
  "TechComponents Ltd",
  "Asia Pacific Trading",
];

// Risk Level Badge
const RiskBadge = ({ level }) => {
  const config = {
    low: { color: "#10b981", bg: "rgba(16, 185, 129, 0.15)", icon: CheckCircle2 },
    medium: { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)", icon: AlertCircle },
    high: { color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)", icon: AlertTriangle },
    critical: { color: "#dc2626", bg: "rgba(220, 38, 38, 0.25)", icon: XCircle },
  };
  
  const cfg = config[level] || config.medium;
  const Icon = cfg.icon;
  
  return (
    <div 
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full"
      style={{ backgroundColor: cfg.bg }}
    >
      <Icon className="w-4 h-4" style={{ color: cfg.color }} />
      <span className="text-sm font-semibold capitalize" style={{ color: cfg.color }}>
        {level} Risk
      </span>
    </div>
  );
};

// Analysis Step Component
const AnalysisStep = ({ step, isActive, isComplete }) => (
  <div className={`flex items-center gap-3 p-3 rounded-lg ${isActive ? 'bg-indigo-500/10' : ''}`}>
    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
      isComplete ? 'bg-emerald-500/20' : isActive ? 'bg-indigo-500/20' : 'bg-zinc-800'
    }`}>
      {isComplete ? (
        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
      ) : isActive ? (
        <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
      ) : (
        <div className="w-2 h-2 rounded-full bg-zinc-600" />
      )}
    </div>
    <span className={`text-sm ${isActive ? 'text-white' : isComplete ? 'text-zinc-400' : 'text-zinc-600'}`}>
      {step}
    </span>
  </div>
);

export default function SupplierRiskDemo() {
  const [supplierName, setSupplierName] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState(null);

  const analysisSteps = [
    "Initializing Supplier Agent",
    "Gathering market intelligence",
    "Analyzing financial indicators",
    "Processing news sentiment",
    "LLM reasoning & risk assessment",
    "Generating recommendations"
  ];

  const handleAnalyze = async () => {
    if (!supplierName.trim()) {
      toast.error("Please enter a supplier name");
      return;
    }

    setAnalyzing(true);
    setResult(null);
    setCurrentStep(0);

    // Simulate step progression
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < analysisSteps.length - 1) return prev + 1;
        clearInterval(stepInterval);
        return prev;
      });
    }, 800);

    try {
      const response = await axios.post(`${API}/supplier-risk/analyze`, {
        supplier_name: supplierName,
        include_news: true
      });
      
      clearInterval(stepInterval);
      setCurrentStep(analysisSteps.length);
      setResult(response.data);
      toast.success("Analysis complete!");
    } catch (error) {
      clearInterval(stepInterval);
      console.error("Analysis failed:", error);
      toast.error("Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="supplier-risk-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Supplier Risk Demo</h1>
        <p className="text-zinc-500 mt-1">Interactive demonstration of AI-powered supplier risk detection</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Input Section */}
        <div className="col-span-5 space-y-6">
          {/* Search Card */}
          <div className="p-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50" data-testid="search-section">
            <h3 className="text-lg font-semibold text-white mb-4">Analyze Supplier</h3>
            
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <Input
                  placeholder="Enter supplier name..."
                  value={supplierName}
                  onChange={(e) => setSupplierName(e.target.value)}
                  className="pl-10 bg-zinc-950 border-zinc-800"
                  data-testid="supplier-input"
                  onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                />
              </div>

              <Button 
                onClick={handleAnalyze}
                disabled={analyzing}
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                data-testid="analyze-btn"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Analyze Risk
                  </>
                )}
              </Button>
            </div>

            {/* Quick Select */}
            <div className="mt-4">
              <p className="text-xs text-zinc-500 mb-2">Quick select:</p>
              <div className="flex flex-wrap gap-2">
                {sampleSuppliers.map((supplier) => (
                  <button
                    key={supplier}
                    onClick={() => setSupplierName(supplier)}
                    className="px-3 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 rounded-full text-zinc-400 hover:text-white transition-colors"
                    data-testid={`quick-select-${supplier.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    {supplier}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Analysis Progress */}
          <div className="p-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50" data-testid="analysis-progress">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Bot className="w-5 h-5 text-indigo-400" />
              Agent Activity
            </h3>
            
            <div className="space-y-1">
              {analysisSteps.map((step, idx) => (
                <AnalysisStep
                  key={idx}
                  step={step}
                  isActive={analyzing && currentStep === idx}
                  isComplete={currentStep > idx}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="col-span-7">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
                data-testid="analysis-result"
              >
                {/* Risk Summary Card */}
                <div className="p-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-white">{result.supplier_name}</h2>
                      <p className="text-sm text-zinc-500">
                        Analysis completed at {new Date(result.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <RiskBadge level={result.risk_level} />
                  </div>

                  {/* Risk Score */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-zinc-400">Risk Score</span>
                      <span className="text-2xl font-bold font-mono text-white">
                        {result.risk_score.toFixed(1)}%
                      </span>
                    </div>
                    <Progress 
                      value={result.risk_score} 
                      className="h-2"
                      style={{
                        '--progress-background': result.risk_score > 70 ? '#ef4444' : 
                          result.risk_score > 40 ? '#f59e0b' : '#10b981'
                      }}
                    />
                  </div>

                  {/* Risk Factors */}
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                      Risk Factors Identified
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {result.risk_factors.map((factor, idx) => (
                        <Badge 
                          key={idx}
                          variant="outline"
                          className="border-amber-500/50 text-amber-400"
                        >
                          <AlertCircle className="w-3 h-3 mr-1" />
                          {factor}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                    <h3 className="text-sm font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      AI Recommendation
                    </h3>
                    <p className="text-sm text-zinc-300">{result.recommendation}</p>
                  </div>
                </div>

                {/* LLM Reasoning */}
                <div className="p-6 bg-zinc-900/50 rounded-xl border border-zinc-800/50" data-testid="llm-reasoning">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-indigo-400" />
                    LLM Reasoning (Ollama Llama3)
                  </h3>
                  <ScrollArea className="h-48">
                    <pre className="text-sm text-zinc-400 font-mono whitespace-pre-wrap">
                      {result.llm_reasoning}
                    </pre>
                  </ScrollArea>
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-96 flex flex-col items-center justify-center text-zinc-500 bg-zinc-900/30 rounded-xl border border-zinc-800/50"
                data-testid="empty-state"
              >
                <AlertTriangle className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg mb-2">No Analysis Results</p>
                <p className="text-sm text-zinc-600">Enter a supplier name and click Analyze Risk to begin</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* How It Works */}
      <div className="p-6 bg-zinc-900/30 rounded-xl border border-zinc-800/50" data-testid="how-it-works">
        <h3 className="text-lg font-semibold text-white mb-4">How It Works</h3>
        <div className="grid grid-cols-4 gap-6">
          {[
            { 
              icon: Search, 
              title: "Data Collection", 
              desc: "Gather supplier data from multiple sources including news, financials, and performance metrics" 
            },
            { 
              icon: Bot, 
              title: "Agent Analysis", 
              desc: "Supplier Agent processes data and extracts risk indicators using ML models" 
            },
            { 
              icon: Zap, 
              title: "LLM Reasoning", 
              desc: "Ollama Llama3 provides contextual reasoning and generates insights from unstructured data" 
            },
            { 
              icon: CheckCircle2, 
              title: "Decision Output", 
              desc: "Risk score calculated with actionable recommendations for supply chain managers" 
            },
          ].map((step, idx) => (
            <div key={idx} className="relative">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center mb-3">
                <step.icon className="w-5 h-5 text-indigo-400" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">{step.title}</h4>
              <p className="text-xs text-zinc-500">{step.desc}</p>
              {idx < 3 && (
                <ArrowRight className="absolute top-4 -right-3 w-6 h-6 text-zinc-700" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
