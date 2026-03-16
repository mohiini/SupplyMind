from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from enum import Enum
import json
import asyncio
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Ollama Configuration
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')

# Create the main app
app = FastAPI(title="SupplyMind API", description="Agentic AI Operating System for Supply Chain Intelligence")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== MODELS =====================

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    DEMAND = "demand"
    INVENTORY = "inventory"
    SUPPLIER = "supplier"
    ACTION = "action"

class WorkflowCategory(str, Enum):
    CUSTOMER = "customer"
    OPERATIONS = "operations"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS = "business"
    SUSTAINABILITY = "sustainability"

class WorkflowType(str, Enum):
    EXECUTION = "execution"
    EFFICIENCY = "efficiency"
    EXCEPTION = "exception"
    EXPANSION = "expansion"

class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Request/Response Models
class AgentMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    agent: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    last_action: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

class Workflow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: WorkflowCategory
    workflow_type: WorkflowType
    agents_involved: List[AgentRole]
    is_active: bool = True
    metrics: Dict[str, Any] = Field(default_factory=dict)

class SupplierRiskRequest(BaseModel):
    supplier_name: str
    include_news: bool = True

class SupplierRiskResponse(BaseModel):
    supplier_name: str
    risk_level: RiskLevel
    risk_score: float
    risk_factors: List[str]
    news_summary: Optional[str] = None
    llm_reasoning: str
    recommendation: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    sku: str
    quantity: int
    reorder_point: int
    safety_stock: int
    warehouse: str
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DemandForecast(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    forecast_period: str
    predicted_demand: int
    confidence_interval: Dict[str, int]
    seasonality_factor: float
    trend: str

class SystemMetrics(BaseModel):
    total_workflows: int = 10
    active_agents: int = 5
    decisions_today: int = 0
    cost_savings: float = 0.0
    risk_alerts: int = 0
    inventory_health: float = 0.0

class OrchestratorRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    task_id: str
    status: str
    orchestrator_reasoning: str
    agent_responses: Dict[str, Any]
    final_decision: str
    actions_taken: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReportRequest(BaseModel):
    report_type: str = "master"  # master, slides, poster

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

# ===================== OLLAMA SERVICE =====================

class OllamaService:
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self.timeout = 120
    
    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.host}/")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Send chat request to Ollama"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "No response")
                else:
                    logger.error(f"Ollama error: {response.status_code}")
                    return self._get_mock_response(messages[-1].get("content", ""))
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return self._get_mock_response(messages[-1].get("content", ""))
    
    def _get_mock_response(self, prompt: str) -> str:
        """Return mock response when Ollama is unavailable"""
        if "risk" in prompt.lower():
            return json.dumps({
                "analysis": "Based on simulated market analysis, potential supply chain disruptions detected.",
                "risk_level": "medium",
                "factors": ["Market volatility", "Supplier capacity constraints", "Logistics delays"],
                "recommendation": "Consider diversifying supplier base and increasing safety stock."
            })
        elif "demand" in prompt.lower():
            return json.dumps({
                "forecast": "Demand expected to increase by 15% in Q2",
                "confidence": 0.82,
                "factors": ["Seasonal trends", "Market growth", "Promotional activities"],
                "recommendation": "Adjust inventory levels accordingly."
            })
        elif "inventory" in prompt.lower():
            return json.dumps({
                "analysis": "Current inventory levels are within optimal range",
                "reorder_suggestion": "Consider reordering SKU-001 within 5 days",
                "optimization": "Reduce safety stock for slow-moving items by 10%"
            })
        else:
            return json.dumps({
                "status": "Analysis complete",
                "insights": ["Multi-agent coordination successful", "All systems operational"],
                "recommendation": "Continue monitoring supply chain metrics."
            })

ollama_service = OllamaService()

# ===================== VALIDATION LAYER =====================

class ValidationLayer:
    """State-wise validation for all operations"""
    
    @staticmethod
    def validate_supplier_risk_request(request: SupplierRiskRequest) -> ValidationResult:
        errors = []
        warnings = []
        
        if not request.supplier_name or len(request.supplier_name.strip()) < 2:
            errors.append("Supplier name must be at least 2 characters")
        
        if len(request.supplier_name) > 100:
            errors.append("Supplier name too long (max 100 characters)")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    @staticmethod
    def validate_orchestrator_request(request: OrchestratorRequest) -> ValidationResult:
        errors = []
        warnings = []
        
        if not request.task or len(request.task.strip()) < 5:
            errors.append("Task description must be at least 5 characters")
        
        if len(request.task) > 1000:
            warnings.append("Task description is very long, consider being more concise")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    @staticmethod
    def validate_llm_output(output: str, expected_format: str = "json") -> ValidationResult:
        """Validate LLM output format and content"""
        errors = []
        warnings = []
        
        if not output or len(output.strip()) == 0:
            errors.append("LLM returned empty response")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        if expected_format == "json":
            try:
                parsed = json.loads(output)
                if not isinstance(parsed, dict):
                    warnings.append("LLM output is valid JSON but not a dictionary")
            except json.JSONDecodeError:
                warnings.append("LLM output is not valid JSON, using raw text")
        
        # Check for harmful content
        harmful_keywords = ["error", "exception", "failed", "invalid"]
        if any(kw in output.lower() for kw in harmful_keywords):
            warnings.append("LLM output may contain error indicators")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    @staticmethod
    def validate_agent_state_transition(current_state: AgentStatus, new_state: AgentStatus) -> ValidationResult:
        """Validate agent state transitions"""
        valid_transitions = {
            AgentStatus.IDLE: [AgentStatus.THINKING, AgentStatus.WAITING],
            AgentStatus.THINKING: [AgentStatus.ACTING, AgentStatus.IDLE, AgentStatus.WAITING],
            AgentStatus.ACTING: [AgentStatus.IDLE, AgentStatus.THINKING],
            AgentStatus.WAITING: [AgentStatus.IDLE, AgentStatus.THINKING]
        }
        
        errors = []
        if new_state not in valid_transitions.get(current_state, []):
            errors.append(f"Invalid state transition from {current_state} to {new_state}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

validation_layer = ValidationLayer()

# ===================== MULTI-AGENT SYSTEM =====================

class AgentMessageBus:
    """Shared message bus for agent communication"""
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.agent_states: Dict[AgentRole, AgentState] = {
            role: AgentState(agent=role) for role in AgentRole
        }
    
    def send_message(self, message: AgentMessage):
        self.messages.append(message)
        logger.info(f"Message from {message.from_agent} to {message.to_agent}: {message.message_type}")
    
    def get_messages_for_agent(self, agent: AgentRole) -> List[AgentMessage]:
        return [m for m in self.messages if m.to_agent == agent]
    
    def update_agent_state(self, agent: AgentRole, status: AgentStatus, task: Optional[str] = None):
        if agent in self.agent_states:
            current_status = self.agent_states[agent].status
            validation = validation_layer.validate_agent_state_transition(current_status, status)
            if validation.is_valid:
                self.agent_states[agent].status = status
                self.agent_states[agent].current_task = task
            else:
                logger.warning(f"Invalid state transition: {validation.errors}")
    
    def get_all_states(self) -> Dict[str, AgentState]:
        return {role.value: state for role, state in self.agent_states.items()}
    
    def clear_messages(self):
        self.messages = []

message_bus = AgentMessageBus()

class MultiAgentOrchestrator:
    """Orchestrates multiple AI agents for supply chain tasks"""
    
    def __init__(self, ollama: OllamaService, bus: AgentMessageBus):
        self.ollama = ollama
        self.bus = bus
        self.agent_prompts = {
            AgentRole.ORCHESTRATOR: """You are the Orchestrator Agent for SupplyMind, an AI-powered supply chain OS.
Your role is to coordinate other agents (Demand, Inventory, Supplier, Action) to complete supply chain tasks.
Analyze the task and determine which agents need to be involved. Return JSON with your coordination plan.""",
            
            AgentRole.DEMAND: """You are the Demand Agent. Your responsibilities:
- Demand forecasting using historical data
- Stockout prediction and prevention
- Demand anomaly detection
Analyze the request and provide demand-related insights in JSON format.""",
            
            AgentRole.INVENTORY: """You are the Inventory Agent. Your responsibilities:
- Reorder point calculation
- Safety stock optimization
- Warehouse balancing across locations
Analyze inventory status and provide optimization recommendations in JSON format.""",
            
            AgentRole.SUPPLIER: """You are the Supplier Agent. Your responsibilities:
- Supplier risk scoring and monitoring
- Shipping mode optimization
- Vendor performance tracking
Assess supplier-related aspects and provide risk analysis in JSON format.""",
            
            AgentRole.ACTION: """You are the Action Agent. Your responsibilities:
- Execute purchase orders
- Send alerts and notifications
- Generate reports and log decisions
Based on other agents' recommendations, determine actions to take and return in JSON format."""
        }
    
    async def process_task(self, task: str, context: Optional[Dict] = None) -> OrchestratorResponse:
        """Process a task through the multi-agent system"""
        task_id = str(uuid.uuid4())
        agent_responses = {}
        actions_taken = []
        
        # Step 1: Orchestrator analyzes the task
        self.bus.update_agent_state(AgentRole.ORCHESTRATOR, AgentStatus.THINKING, task)
        
        orchestrator_prompt = f"""
Task: {task}
Context: {json.dumps(context) if context else 'None'}

Analyze this supply chain task and create a coordination plan.
Return JSON with:
- agents_to_involve: list of agents needed
- sequence: order of agent invocations
- key_questions: what each agent should analyze
"""
        
        orchestrator_response = await self.ollama.chat([
            {"role": "system", "content": self.agent_prompts[AgentRole.ORCHESTRATOR]},
            {"role": "user", "content": orchestrator_prompt}
        ], temperature=0.3)
        
        # Validate LLM output
        llm_validation = validation_layer.validate_llm_output(orchestrator_response)
        if not llm_validation.is_valid:
            logger.warning(f"LLM output validation warnings: {llm_validation.warnings}")
        
        agent_responses["orchestrator"] = orchestrator_response
        self.bus.update_agent_state(AgentRole.ORCHESTRATOR, AgentStatus.ACTING)
        
        # Step 2: Invoke relevant agents based on task type
        task_lower = task.lower()
        
        if "demand" in task_lower or "forecast" in task_lower:
            self.bus.update_agent_state(AgentRole.DEMAND, AgentStatus.THINKING, "Analyzing demand")
            demand_response = await self._invoke_agent(AgentRole.DEMAND, task, context)
            agent_responses["demand"] = demand_response
            self.bus.update_agent_state(AgentRole.DEMAND, AgentStatus.IDLE)
        
        if "inventory" in task_lower or "stock" in task_lower:
            self.bus.update_agent_state(AgentRole.INVENTORY, AgentStatus.THINKING, "Checking inventory")
            inventory_response = await self._invoke_agent(AgentRole.INVENTORY, task, context)
            agent_responses["inventory"] = inventory_response
            self.bus.update_agent_state(AgentRole.INVENTORY, AgentStatus.IDLE)
        
        if "supplier" in task_lower or "risk" in task_lower:
            self.bus.update_agent_state(AgentRole.SUPPLIER, AgentStatus.THINKING, "Assessing suppliers")
            supplier_response = await self._invoke_agent(AgentRole.SUPPLIER, task, context)
            agent_responses["supplier"] = supplier_response
            self.bus.update_agent_state(AgentRole.SUPPLIER, AgentStatus.IDLE)
        
        # Step 3: Action agent determines final actions
        self.bus.update_agent_state(AgentRole.ACTION, AgentStatus.THINKING, "Planning actions")
        action_prompt = f"""
Based on the following agent analyses:
{json.dumps(agent_responses, indent=2)}

Determine what actions should be taken. Return JSON with:
- actions: list of specific actions
- priority: urgency level
- notifications: who should be notified
"""
        
        action_response = await self.ollama.chat([
            {"role": "system", "content": self.agent_prompts[AgentRole.ACTION]},
            {"role": "user", "content": action_prompt}
        ], temperature=0.3)
        
        agent_responses["action"] = action_response
        self.bus.update_agent_state(AgentRole.ACTION, AgentStatus.IDLE)
        
        # Parse actions from response
        try:
            action_data = json.loads(action_response)
            actions_taken = action_data.get("actions", ["Analysis complete", "Recommendations generated"])
        except:
            actions_taken = ["Analysis complete", "Recommendations generated"]
        
        # Reset orchestrator
        self.bus.update_agent_state(AgentRole.ORCHESTRATOR, AgentStatus.IDLE)
        
        return OrchestratorResponse(
            task_id=task_id,
            status="completed",
            orchestrator_reasoning=orchestrator_response,
            agent_responses=agent_responses,
            final_decision=f"Task '{task}' processed successfully",
            actions_taken=actions_taken
        )
    
    async def _invoke_agent(self, agent: AgentRole, task: str, context: Optional[Dict]) -> str:
        prompt = f"""
Task: {task}
Context: {json.dumps(context) if context else 'None'}

Provide your analysis and recommendations in JSON format.
"""
        return await self.ollama.chat([
            {"role": "system", "content": self.agent_prompts[agent]},
            {"role": "user", "content": prompt}
        ], temperature=0.5)

orchestrator = MultiAgentOrchestrator(ollama_service, message_bus)

# ===================== WORKFLOWS DATA =====================

WORKFLOWS = [
    Workflow(
        id="wf-1", name="Demand Forecasting", 
        description="Predict future product demand using historical data, market trends, and ML models",
        category=WorkflowCategory.CUSTOMER, workflow_type=WorkflowType.EFFICIENCY,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.DEMAND],
        metrics={"accuracy": 0.92, "mape": 8.5}
    ),
    Workflow(
        id="wf-2", name="Inventory Optimization",
        description="Optimize inventory levels across warehouses to minimize costs while preventing stockouts",
        category=WorkflowCategory.OPERATIONS, workflow_type=WorkflowType.EFFICIENCY,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.INVENTORY, AgentRole.DEMAND],
        metrics={"turnover_rate": 12.5, "fill_rate": 0.97}
    ),
    Workflow(
        id="wf-3", name="Warehouse Automation",
        description="Automate warehouse operations including picking, packing, and storage optimization",
        category=WorkflowCategory.INFRASTRUCTURE, workflow_type=WorkflowType.EXECUTION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.INVENTORY, AgentRole.ACTION],
        metrics={"automation_rate": 0.78, "pick_accuracy": 0.995}
    ),
    Workflow(
        id="wf-4", name="Route Optimization",
        description="Optimize delivery routes to minimize transportation costs and delivery times",
        category=WorkflowCategory.OPERATIONS, workflow_type=WorkflowType.EFFICIENCY,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER, AgentRole.ACTION],
        metrics={"cost_reduction": 0.23, "on_time_delivery": 0.94}
    ),
    Workflow(
        id="wf-5", name="Shipment Delay Prediction",
        description="Predict potential shipment delays using real-time tracking and external factors",
        category=WorkflowCategory.OPERATIONS, workflow_type=WorkflowType.EXCEPTION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER],
        metrics={"prediction_accuracy": 0.88, "lead_time_variance": 2.3}
    ),
    Workflow(
        id="wf-6", name="Supplier Risk Detection",
        description="Monitor and assess supplier risks including financial health, geopolitical factors, and performance",
        category=WorkflowCategory.BUSINESS, workflow_type=WorkflowType.EXCEPTION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER, AgentRole.ACTION],
        metrics={"risk_alerts": 12, "supplier_score_avg": 7.8}
    ),
    Workflow(
        id="wf-7", name="Procurement Automation",
        description="Automate procurement processes including RFQ generation, vendor selection, and PO creation",
        category=WorkflowCategory.BUSINESS, workflow_type=WorkflowType.EXECUTION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER, AgentRole.ACTION],
        metrics={"cycle_time_days": 5.2, "cost_savings": 0.18}
    ),
    Workflow(
        id="wf-8", name="Logistics Cost Optimization",
        description="Analyze and optimize logistics costs across transportation, warehousing, and handling",
        category=WorkflowCategory.BUSINESS, workflow_type=WorkflowType.EFFICIENCY,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER, AgentRole.INVENTORY],
        metrics={"total_cost_reduction": 0.15, "logistics_ratio": 0.08}
    ),
    Workflow(
        id="wf-9", name="Production Planning",
        description="Plan and schedule production based on demand forecasts and resource availability",
        category=WorkflowCategory.OPERATIONS, workflow_type=WorkflowType.EXECUTION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.DEMAND, AgentRole.INVENTORY],
        metrics={"schedule_adherence": 0.91, "capacity_utilization": 0.84}
    ),
    Workflow(
        id="wf-10", name="Sustainability Tracking",
        description="Monitor and report on supply chain sustainability metrics including carbon footprint",
        category=WorkflowCategory.SUSTAINABILITY, workflow_type=WorkflowType.EXPANSION,
        agents_involved=[AgentRole.ORCHESTRATOR, AgentRole.SUPPLIER, AgentRole.ACTION],
        metrics={"carbon_reduction": 0.12, "sustainable_suppliers": 0.45}
    ),
]

# ===================== API ROUTES =====================

@api_router.get("/")
async def root():
    return {"message": "SupplyMind API - Agentic AI Operating System for Supply Chain Intelligence"}

@api_router.get("/health")
async def health_check():
    """Check system health including Ollama status"""
    ollama_status = await ollama_service.health_check()
    return {
        "status": "healthy",
        "ollama_connected": ollama_status,
        "model": OLLAMA_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Agent Routes
@api_router.get("/agents/states")
async def get_agent_states():
    """Get current state of all agents"""
    states = message_bus.get_all_states()
    return {"agents": {k: v.model_dump() for k, v in states.items()}}

@api_router.get("/agents/messages")
async def get_agent_messages(limit: int = 50):
    """Get recent agent messages"""
    messages = message_bus.messages[-limit:]
    return {"messages": [m.model_dump() for m in messages], "count": len(messages)}

# Workflow Routes
@api_router.get("/workflows")
async def get_workflows():
    """Get all supply chain workflows"""
    return {"workflows": [w.model_dump() for w in WORKFLOWS], "count": len(WORKFLOWS)}

@api_router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow details"""
    workflow = next((w for w in WORKFLOWS if w.id == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()

# Orchestrator Routes
@api_router.post("/orchestrator/process")
async def process_orchestrator_task(request: OrchestratorRequest):
    """Process a task through the multi-agent orchestrator"""
    # Validate request
    validation = validation_layer.validate_orchestrator_request(request)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})
    
    response = await orchestrator.process_task(request.task, request.context)
    
    # Store in database
    doc = response.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.orchestrator_tasks.insert_one(doc)
    
    return response.model_dump()

# Supplier Risk Demo
@api_router.post("/supplier-risk/analyze", response_model=dict)
async def analyze_supplier_risk(request: SupplierRiskRequest):
    """Analyze supplier risk using AI agents"""
    # Validate request
    validation = validation_layer.validate_supplier_risk_request(request)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})
    
    # Update agent states
    message_bus.update_agent_state(AgentRole.SUPPLIER, AgentStatus.THINKING, f"Analyzing {request.supplier_name}")
    
    # Simulate news gathering
    simulated_news = [
        {"source": "Reuters", "headline": f"Supply chain disruptions affect {request.supplier_name} operations", "sentiment": "negative"},
        {"source": "Bloomberg", "headline": f"{request.supplier_name} announces expansion plans", "sentiment": "positive"},
        {"source": "WSJ", "headline": "Global shipping delays continue to impact manufacturers", "sentiment": "negative"},
    ]
    
    # Create prompt for LLM analysis
    risk_prompt = f"""
Analyze the supplier risk for: {request.supplier_name}

Recent news:
{json.dumps(simulated_news, indent=2)}

Provide a comprehensive risk assessment in JSON format with:
- risk_level: one of [low, medium, high, critical]
- risk_score: number between 0-100
- risk_factors: list of specific risk factors identified
- news_impact: summary of how news affects risk
- recommendation: specific action to take

Be thorough in your analysis.
"""
    
    llm_response = await ollama_service.chat([
        {"role": "system", "content": "You are a supply chain risk analyst. Provide detailed, actionable risk assessments in JSON format."},
        {"role": "user", "content": risk_prompt}
    ], temperature=0.4)
    
    # Validate LLM output
    llm_validation = validation_layer.validate_llm_output(llm_response, "json")
    
    # Parse response
    try:
        risk_data = json.loads(llm_response)
        risk_level = RiskLevel(risk_data.get("risk_level", "medium"))
        risk_score = float(risk_data.get("risk_score", 50))
        risk_factors = risk_data.get("risk_factors", ["Market volatility", "Supply chain disruptions"])
        recommendation = risk_data.get("recommendation", "Monitor supplier closely and maintain backup options")
    except (json.JSONDecodeError, ValueError):
        risk_level = RiskLevel.MEDIUM
        risk_score = 55.0
        risk_factors = ["Potential supply chain disruptions", "Market uncertainty", "Geopolitical factors"]
        recommendation = "Maintain close monitoring and consider diversification"
    
    message_bus.update_agent_state(AgentRole.SUPPLIER, AgentStatus.IDLE)
    
    response = SupplierRiskResponse(
        supplier_name=request.supplier_name,
        risk_level=risk_level,
        risk_score=risk_score,
        risk_factors=risk_factors,
        news_summary="Analysis based on simulated market news and AI reasoning" if request.include_news else None,
        llm_reasoning=llm_response,
        recommendation=recommendation
    )
    
    # Store in database
    doc = response.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.supplier_risk_analyses.insert_one(doc)
    
    return response.model_dump()

# Metrics Routes
@api_router.get("/metrics/system")
async def get_system_metrics():
    """Get system-wide metrics"""
    # Calculate metrics from database
    decisions_count = await db.orchestrator_tasks.count_documents({})
    risk_alerts = await db.supplier_risk_analyses.count_documents({"risk_level": {"$in": ["high", "critical"]}})
    
    return SystemMetrics(
        total_workflows=len(WORKFLOWS),
        active_agents=5,
        decisions_today=decisions_count,
        cost_savings=234500.0,
        risk_alerts=risk_alerts,
        inventory_health=92.5
    ).model_dump()

@api_router.get("/metrics/kpis")
async def get_kpis():
    """Get key performance indicators"""
    return {
        "kpis": [
            {"name": "Cost Savings", "value": "$234.5K", "change": 12.5, "trend": "up"},
            {"name": "On-Time Delivery", "value": "94.2%", "change": 2.3, "trend": "up"},
            {"name": "Inventory Turnover", "value": "12.5x", "change": -0.8, "trend": "down"},
            {"name": "Supplier Risk Score", "value": "7.8/10", "change": 0.4, "trend": "up"},
            {"name": "Forecast Accuracy", "value": "92%", "change": 3.1, "trend": "up"},
            {"name": "Carbon Footprint", "value": "-12%", "change": 4.2, "trend": "up"},
        ]
    }

# Report Generation
@api_router.get("/reports/master")
async def get_master_report():
    """Get master report content for the project"""
    return {
        "title": "SupplyMind: Agentic AI Operating System for Supply Chain Intelligence",
        "sections": [
            {
                "id": "executive-summary",
                "title": "Executive Summary",
                "content": """SupplyMind is an Agentic AI Operating System that autonomously orchestrates global supply chains using multi-agent AI systems. The system transforms reactive supply chains into autonomous decision-making ecosystems, addressing critical challenges including demand volatility, inventory imbalance, supplier risk, logistics delays, and rising costs.

Key innovations include:
- LLM-orchestrated multi-agent architecture with specialized agents for demand, inventory, supplier, and action management
- Hybrid ML + LLM decision systems combining classical forecasting with generative AI reasoning
- Real-time supply chain visibility with autonomous exception handling
- 15-25% cost reduction through optimized operations"""
            },
            {
                "id": "problem-statement",
                "title": "Problem Statement",
                "content": """Modern supply chains face unprecedented complexity:
- 73% of companies experienced supply chain disruptions in the past year
- Average inventory carrying cost is 20-30% of inventory value
- Manual decision-making leads to 2-3 week response delays
- Lack of real-time visibility causes 15-20% revenue loss

Traditional systems fail because they:
- Operate in silos without cross-functional optimization
- React to problems instead of predicting them
- Cannot process unstructured data (news, reports)
- Lack autonomous decision-making capabilities"""
            },
            {
                "id": "solution-architecture",
                "title": "Solution: Agentic AI Architecture",
                "content": """SupplyMind implements a multi-agent architecture with 5 specialized agents:

1. **Orchestrator Agent** (LLM-driven): Coordinates all agents, decomposes complex tasks, manages workflow execution
2. **Demand Agent**: Forecasting, stockout prediction, anomaly detection
3. **Inventory Agent**: Reorder points, safety stock, warehouse balancing
4. **Supplier Agent**: Risk scoring, shipping optimization, vendor monitoring
5. **Action Agent**: Purchase orders, alerts, reports, decision logging

Agents communicate via a shared message bus using JSON state, enabling:
- Parallel processing of independent tasks
- Sequential orchestration for dependent operations
- Real-time state synchronization
- Audit trail of all decisions"""
            },
            {
                "id": "workflows",
                "title": "10 Supply Chain Workflows",
                "content": """1. Demand Forecasting (Customer/Efficiency)
2. Inventory Optimization (Operations/Efficiency)
3. Warehouse Automation (Infrastructure/Execution)
4. Route Optimization (Operations/Efficiency)
5. Shipment Delay Prediction (Operations/Exception)
6. Supplier Risk Detection (Business/Exception)
7. Procurement Automation (Business/Execution)
8. Logistics Cost Optimization (Business/Efficiency)
9. Production Planning (Operations/Execution)
10. Sustainability Tracking (Sustainability/Expansion)"""
            },
            {
                "id": "roi-analysis",
                "title": "ROI Analysis",
                "content": """Projected ROI for mid-size enterprise ($500M revenue):

Direct Cost Savings:
- Inventory reduction: $2.5M (15% reduction in carrying costs)
- Logistics optimization: $1.8M (12% transportation savings)
- Procurement efficiency: $800K (reduced maverick spending)

Operational Improvements:
- 40% faster response to disruptions
- 25% improvement in forecast accuracy
- 60% reduction in manual planning effort

Total Annual Benefit: $5.1M
Implementation Cost: $1.2M
Payback Period: 2.8 months
3-Year ROI: 425%"""
            },
            {
                "id": "patentability",
                "title": "Patentability & Innovation",
                "content": """Novel innovations worthy of patent protection:

1. **Multi-Agent Supply Chain Orchestration System**: Method for coordinating specialized AI agents to autonomously manage supply chain operations using LLM-based reasoning

2. **Hybrid ML-LLM Decision Engine**: System combining classical machine learning forecasts with LLM reasoning for supply chain optimization

3. **Real-Time Risk Propagation Analysis**: Method for assessing cascading effects of supply chain disruptions using agent-based simulation

4. **Autonomous Procurement Execution**: System for end-to-end procurement automation including vendor selection, negotiation, and PO generation"""
            }
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/reports/slides")
async def get_slides_content():
    """Get slide deck content"""
    return {
        "title": "SupplyMind Pitch Deck",
        "slides": [
            {
                "number": 1,
                "title": "SupplyMind",
                "subtitle": "Agentic AI Operating System for Supply Chain Intelligence",
                "bullets": ["Transform reactive supply chains into autonomous ecosystems", "Multi-agent AI architecture", "Real-time decision optimization"]
            },
            {
                "number": 2,
                "title": "The Problem",
                "bullets": ["73% of companies faced supply chain disruptions", "20-30% inventory carrying costs", "2-3 week decision delays", "15-20% revenue loss from poor visibility"]
            },
            {
                "number": 3,
                "title": "Our Solution",
                "bullets": ["5 Specialized AI Agents working in coordination", "LLM-powered reasoning + ML forecasting", "Autonomous decision execution", "Real-time supply chain visibility"]
            },
            {
                "number": 4,
                "title": "Multi-Agent Architecture",
                "bullets": ["Orchestrator: Task coordination & planning", "Demand Agent: Forecasting & predictions", "Inventory Agent: Stock optimization", "Supplier Agent: Risk management", "Action Agent: Execution & reporting"]
            },
            {
                "number": 5,
                "title": "10 Workflows",
                "bullets": ["Demand Forecasting & Inventory Optimization", "Warehouse Automation & Route Optimization", "Shipment Prediction & Supplier Risk", "Procurement & Logistics Cost", "Production Planning & Sustainability"]
            },
            {
                "number": 6,
                "title": "Technical Innovation",
                "bullets": ["Hybrid ML + LLM decision systems", "Real-time agent message bus", "Autonomous exception handling", "Natural language supply chain queries"]
            },
            {
                "number": 7,
                "title": "Business Impact",
                "bullets": ["15% inventory cost reduction", "12% logistics savings", "40% faster disruption response", "25% forecast accuracy improvement"]
            },
            {
                "number": 8,
                "title": "ROI Analysis",
                "bullets": ["Annual benefit: $5.1M (mid-size enterprise)", "Implementation: $1.2M", "Payback: 2.8 months", "3-Year ROI: 425%"]
            },
            {
                "number": 9,
                "title": "Roadmap",
                "bullets": ["Year 0-1: MVP (Risk Detection, Delay Prediction)", "Year 1-2: Full Optimization Suite", "Year 2-3: Autonomous Procurement OS"]
            },
            {
                "number": 10,
                "title": "The Team & Ask",
                "bullets": ["AI/ML Engineers + Supply Chain Experts", "Seeking: $2M Seed Round", "Contact: team@supplymind.ai"]
            }
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# Inventory Routes
@api_router.get("/inventory")
async def get_inventory():
    """Get inventory items"""
    items = [
        InventoryItem(id="inv-1", product_name="Widget A", sku="SKU-001", quantity=1250, reorder_point=500, safety_stock=200, warehouse="Warehouse-East"),
        InventoryItem(id="inv-2", product_name="Component B", sku="SKU-002", quantity=320, reorder_point=400, safety_stock=150, warehouse="Warehouse-West"),
        InventoryItem(id="inv-3", product_name="Assembly C", sku="SKU-003", quantity=890, reorder_point=300, safety_stock=100, warehouse="Warehouse-East"),
        InventoryItem(id="inv-4", product_name="Part D", sku="SKU-004", quantity=2100, reorder_point=800, safety_stock=300, warehouse="Warehouse-Central"),
        InventoryItem(id="inv-5", product_name="Module E", sku="SKU-005", quantity=450, reorder_point=200, safety_stock=75, warehouse="Warehouse-West"),
    ]
    return {"items": [item.model_dump() for item in items], "count": len(items)}

# Demand Forecast Routes
@api_router.get("/forecasts")
async def get_forecasts():
    """Get demand forecasts"""
    forecasts = [
        DemandForecast(id="fc-1", product_name="Widget A", forecast_period="Q2 2026", predicted_demand=15000, confidence_interval={"low": 13500, "high": 16500}, seasonality_factor=1.15, trend="increasing"),
        DemandForecast(id="fc-2", product_name="Component B", forecast_period="Q2 2026", predicted_demand=8500, confidence_interval={"low": 7800, "high": 9200}, seasonality_factor=0.95, trend="stable"),
        DemandForecast(id="fc-3", product_name="Assembly C", forecast_period="Q2 2026", predicted_demand=12000, confidence_interval={"low": 10800, "high": 13200}, seasonality_factor=1.08, trend="increasing"),
    ]
    return {"forecasts": [f.model_dump() for f in forecasts], "count": len(forecasts)}

# Analytics Data
@api_router.get("/analytics/demand-trend")
async def get_demand_trend():
    """Get historical demand trend data"""
    return {
        "data": [
            {"month": "Aug", "actual": 12500, "forecast": 12000},
            {"month": "Sep", "actual": 13200, "forecast": 13500},
            {"month": "Oct", "actual": 14800, "forecast": 14200},
            {"month": "Nov", "actual": 15500, "forecast": 15800},
            {"month": "Dec", "actual": 18200, "forecast": 17500},
            {"month": "Jan", "actual": 14500, "forecast": 15000},
        ]
    }

@api_router.get("/analytics/inventory-levels")
async def get_inventory_levels():
    """Get inventory levels by warehouse"""
    return {
        "data": [
            {"warehouse": "East", "current": 3200, "optimal": 3500, "safety": 800},
            {"warehouse": "West", "current": 2800, "optimal": 3000, "safety": 600},
            {"warehouse": "Central", "current": 4100, "optimal": 4000, "safety": 1000},
            {"warehouse": "North", "current": 1900, "optimal": 2500, "safety": 500},
        ]
    }

@api_router.get("/analytics/supplier-performance")
async def get_supplier_performance():
    """Get supplier performance metrics"""
    return {
        "data": [
            {"supplier": "Acme Corp", "quality": 94, "delivery": 92, "cost": 88, "risk": 25},
            {"supplier": "Global Parts", "quality": 89, "delivery": 95, "cost": 82, "risk": 35},
            {"supplier": "FastShip Inc", "quality": 91, "delivery": 88, "cost": 90, "risk": 20},
            {"supplier": "MegaSupply", "quality": 86, "delivery": 90, "cost": 95, "risk": 45},
        ]
    }

@api_router.get("/analytics/cost-breakdown")
async def get_cost_breakdown():
    """Get logistics cost breakdown"""
    return {
        "data": [
            {"category": "Transportation", "value": 42, "trend": -5},
            {"category": "Warehousing", "value": 28, "trend": -2},
            {"category": "Handling", "value": 15, "trend": 0},
            {"category": "Packaging", "value": 10, "trend": -1},
            {"category": "Other", "value": 5, "trend": 0},
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
