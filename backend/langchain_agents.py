"""
SupplyMind LangChain Agent System
Multi-agent orchestration using LangChain for supply chain intelligence
"""
import json
import logging
from typing import List, Dict, Any, Optional, Annotated, TypedDict
from datetime import datetime, timezone
from enum import Enum

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

# LangGraph for multi-agent orchestration
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Local imports
from datasets import (
    get_products, get_suppliers, get_warehouses,
    get_demand_by_product, get_inventory_by_product, get_inventory_by_warehouse,
    get_supplier_performance, get_shipments_by_supplier, get_supplier_risk_data,
    get_news_events, get_demand_summary, get_inventory_summary,
    DEMAND_DATA, INVENTORY_DATA, SHIPMENT_DATA, SUPPLIER_PERFORMANCE_DATA
)

logger = logging.getLogger(__name__)

# ============================================================
# AGENT STATE DEFINITION
# ============================================================
class AgentState(TypedDict):
    """State shared between agents"""
    messages: List[Any]
    task: str
    context: Dict[str, Any]
    current_agent: str
    agent_outputs: Dict[str, Any]
    final_response: Optional[str]
    tools_used: List[str]

# ============================================================
# SUPPLY CHAIN TOOLS (LangChain Tools)
# ============================================================

@tool
def forecast_demand(product_id: str, periods: int = 3) -> str:
    """
    Forecast future demand for a product based on historical data.
    Uses time series analysis to predict demand for the next N periods.
    
    Args:
        product_id: The product ID to forecast (e.g., 'PRD-001')
        periods: Number of future periods to forecast (default: 3)
    
    Returns:
        JSON string with forecast results including predictions and confidence intervals
    """
    import pandas as pd
    import numpy as np
    
    demand_data = get_demand_by_product(product_id)
    if not demand_data:
        return json.dumps({"error": f"No data found for product {product_id}"})
    
    df = pd.DataFrame(demand_data)
    
    # Calculate statistics
    avg_demand = df["actual_demand"].mean()
    std_demand = df["actual_demand"].std()
    trend = (df["actual_demand"].iloc[-6:].mean() - df["actual_demand"].iloc[:6].mean()) / df["actual_demand"].iloc[:6].mean()
    
    # Simple forecast with trend
    forecasts = []
    for i in range(periods):
        forecast = avg_demand * (1 + trend * (i + 1) / 12)
        forecasts.append({
            "period": i + 1,
            "forecast": round(forecast),
            "lower_bound": round(forecast - 1.96 * std_demand),
            "upper_bound": round(forecast + 1.96 * std_demand),
            "confidence": 0.95
        })
    
    # Calculate forecast accuracy metrics
    mape = df["forecast_error"].mean()
    
    result = {
        "product_id": product_id,
        "product_name": df["product_name"].iloc[0],
        "historical_avg": round(avg_demand),
        "trend_pct": round(trend * 100, 1),
        "mape": round(mape, 2),
        "forecasts": forecasts,
        "seasonality_detected": True if std_demand / avg_demand > 0.2 else False
    }
    
    return json.dumps(result)


@tool
def analyze_stockout_risk(product_id: str, warehouse_id: str = None) -> str:
    """
    Analyze stockout risk for a product across warehouses.
    Evaluates current inventory levels against demand patterns.
    
    Args:
        product_id: The product ID to analyze
        warehouse_id: Optional specific warehouse (analyzes all if not provided)
    
    Returns:
        JSON string with stockout risk assessment
    """
    inventory = get_inventory_by_product(product_id)
    if warehouse_id:
        inventory = [i for i in inventory if i["warehouse_id"] == warehouse_id]
    
    if not inventory:
        return json.dumps({"error": f"No inventory data for product {product_id}"})
    
    risks = []
    for inv in inventory:
        days_supply = inv["days_of_supply"]
        lead_time = next((p["lead_time_days"] for p in get_products() if p["id"] == product_id), 7)
        
        # Calculate risk level
        if days_supply < lead_time * 0.5:
            risk_level = "critical"
            risk_score = 95
        elif days_supply < lead_time:
            risk_level = "high"
            risk_score = 75
        elif days_supply < lead_time * 1.5:
            risk_level = "medium"
            risk_score = 45
        else:
            risk_level = "low"
            risk_score = 15
        
        risks.append({
            "warehouse": inv["warehouse_name"],
            "current_stock": inv["current_stock"],
            "days_of_supply": inv["days_of_supply"],
            "reorder_point": inv["reorder_point"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "recommendation": f"Reorder immediately" if risk_level in ["critical", "high"] else "Monitor"
        })
    
    return json.dumps({
        "product_id": product_id,
        "stockout_risks": risks,
        "highest_risk": max(risks, key=lambda x: x["risk_score"])
    })


@tool
def calculate_reorder_point(product_id: str, service_level: float = 0.95) -> str:
    """
    Calculate optimal reorder point and safety stock for a product.
    
    Args:
        product_id: The product ID
        service_level: Desired service level (default 0.95 = 95%)
    
    Returns:
        JSON string with reorder calculations
    """
    import numpy as np
    
    demand_data = get_demand_by_product(product_id)
    if not demand_data:
        return json.dumps({"error": f"No data for product {product_id}"})
    
    product = next((p for p in get_products() if p["id"] == product_id), None)
    if not product:
        return json.dumps({"error": "Product not found"})
    
    # Calculate demand statistics
    demands = [d["actual_demand"] for d in demand_data]
    avg_daily_demand = sum(demands) / (len(demands) * 30)  # Monthly to daily
    std_daily_demand = np.std(demands) / 30
    
    lead_time = product["lead_time_days"]
    
    # Z-score for service level
    z_scores = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
    z = z_scores.get(service_level, 1.65)
    
    # Calculate safety stock and reorder point
    safety_stock = z * std_daily_demand * np.sqrt(lead_time)
    reorder_point = (avg_daily_demand * lead_time) + safety_stock
    
    # Economic Order Quantity (EOQ)
    ordering_cost = 50  # Assumed
    holding_cost_rate = 0.25
    annual_demand = avg_daily_demand * 365
    eoq = np.sqrt((2 * annual_demand * ordering_cost) / (product["unit_cost"] * holding_cost_rate))
    
    return json.dumps({
        "product_id": product_id,
        "product_name": product["name"],
        "avg_daily_demand": round(avg_daily_demand, 1),
        "lead_time_days": lead_time,
        "service_level": service_level,
        "safety_stock": round(safety_stock),
        "reorder_point": round(reorder_point),
        "economic_order_quantity": round(eoq),
        "recommendation": f"Set reorder point at {round(reorder_point)} units with safety stock of {round(safety_stock)} units"
    })


@tool
def check_warehouse_levels(warehouse_id: str) -> str:
    """
    Check inventory levels and health for a specific warehouse.
    
    Args:
        warehouse_id: The warehouse ID (e.g., 'WH-EAST')
    
    Returns:
        JSON string with warehouse inventory analysis
    """
    inventory = get_inventory_by_warehouse(warehouse_id)
    if not inventory:
        return json.dumps({"error": f"No data for warehouse {warehouse_id}"})
    
    warehouse = next((w for w in get_warehouses() if w["id"] == warehouse_id), None)
    
    # Analyze inventory health
    critical_items = [i for i in inventory if i["status"] == "Critical"]
    low_items = [i for i in inventory if i["status"] == "Low"]
    overstock_items = [i for i in inventory if i["status"] == "Overstock"]
    optimal_items = [i for i in inventory if i["status"] == "Optimal"]
    
    total_value = sum(i["inventory_value"] for i in inventory)
    total_units = sum(i["current_stock"] for i in inventory)
    
    return json.dumps({
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse["name"] if warehouse else "Unknown",
        "location": warehouse["location"] if warehouse else "Unknown",
        "capacity_utilization": warehouse["utilization"] if warehouse else 0,
        "summary": {
            "total_skus": len(inventory),
            "total_units": total_units,
            "total_value": round(total_value, 2),
            "critical_items": len(critical_items),
            "low_items": len(low_items),
            "optimal_items": len(optimal_items),
            "overstock_items": len(overstock_items)
        },
        "critical_products": [{"product": i["product_name"], "stock": i["current_stock"], "days_supply": i["days_of_supply"]} for i in critical_items[:5]],
        "health_score": round((len(optimal_items) / len(inventory)) * 100, 1) if inventory else 0
    })


@tool
def score_supplier_risk(supplier_id: str) -> str:
    """
    Calculate comprehensive risk score for a supplier.
    Analyzes performance history, shipment data, and external factors.
    
    Args:
        supplier_id: The supplier ID (e.g., 'SUP-001')
    
    Returns:
        JSON string with detailed risk assessment
    """
    risk_data = get_supplier_risk_data(supplier_id)
    if not risk_data:
        return json.dumps({"error": f"No data for supplier {supplier_id}"})
    
    supplier = risk_data["supplier"]
    shipment_stats = risk_data["shipment_stats"]
    news = risk_data["recent_news"]
    
    # Calculate component scores
    performance_score = supplier["reliability_score"]
    delivery_score = supplier["on_time_delivery"]
    quality_score = supplier["quality_rating"] * 20
    
    # Financial health score
    financial_scores = {"Strong": 90, "Moderate": 65, "Developing": 40, "Weak": 20}
    financial_score = financial_scores.get(supplier["financial_health"], 50)
    
    # News sentiment impact
    negative_news = [n for n in news if n["sentiment"] == "negative"]
    news_penalty = len(negative_news) * 5
    
    # Calculate overall risk score (0-100, higher = more risky)
    reliability_component = 100 - performance_score
    delivery_component = 100 - delivery_score
    quality_component = 100 - quality_score
    financial_component = 100 - financial_score
    
    risk_score = (
        reliability_component * 0.25 +
        delivery_component * 0.25 +
        quality_component * 0.20 +
        financial_component * 0.15 +
        news_penalty * 0.15
    )
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return json.dumps({
        "supplier_id": supplier_id,
        "supplier_name": supplier["name"],
        "country": supplier["country"],
        "region": supplier["region"],
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "component_scores": {
            "reliability": round(100 - reliability_component, 1),
            "delivery": round(100 - delivery_component, 1),
            "quality": round(100 - quality_component, 1),
            "financial": round(100 - financial_component, 1)
        },
        "risk_factors": supplier["risk_factors"],
        "shipment_performance": shipment_stats,
        "negative_news_count": len(negative_news),
        "certifications": supplier["certifications"],
        "recommendation": f"{'Immediate action required' if risk_level == 'critical' else 'Close monitoring recommended' if risk_level == 'high' else 'Continue normal monitoring'}"
    })


@tool
def get_shipping_options(supplier_id: str, urgency: str = "normal") -> str:
    """
    Get optimal shipping mode recommendations for a supplier.
    
    Args:
        supplier_id: The supplier ID
        urgency: Urgency level ('urgent', 'normal', 'economy')
    
    Returns:
        JSON string with shipping recommendations
    """
    supplier = next((s for s in get_suppliers() if s["id"] == supplier_id), None)
    if not supplier:
        return json.dumps({"error": f"Supplier {supplier_id} not found"})
    
    region = supplier["region"]
    
    # Define shipping options by region
    options = {
        "Asia Pacific": [
            {"mode": "Air", "transit_days": 5, "cost_factor": 3.5, "reliability": 95},
            {"mode": "Sea", "transit_days": 25, "cost_factor": 1.0, "reliability": 85},
            {"mode": "Air-Sea Combo", "transit_days": 15, "cost_factor": 2.0, "reliability": 90}
        ],
        "Europe": [
            {"mode": "Air", "transit_days": 3, "cost_factor": 3.0, "reliability": 96},
            {"mode": "Sea", "transit_days": 12, "cost_factor": 1.0, "reliability": 88},
            {"mode": "Rail", "transit_days": 18, "cost_factor": 1.5, "reliability": 82}
        ],
        "North America": [
            {"mode": "Ground", "transit_days": 5, "cost_factor": 1.0, "reliability": 94},
            {"mode": "Air", "transit_days": 2, "cost_factor": 2.5, "reliability": 98},
            {"mode": "Rail", "transit_days": 7, "cost_factor": 0.8, "reliability": 90}
        ]
    }
    
    available_options = options.get(region, options["North America"])
    
    # Recommend based on urgency
    if urgency == "urgent":
        recommended = min(available_options, key=lambda x: x["transit_days"])
    elif urgency == "economy":
        recommended = min(available_options, key=lambda x: x["cost_factor"])
    else:
        # Balance cost and time
        recommended = min(available_options, key=lambda x: x["transit_days"] * x["cost_factor"])
    
    return json.dumps({
        "supplier_id": supplier_id,
        "supplier_name": supplier["name"],
        "origin_region": region,
        "urgency": urgency,
        "recommended_option": recommended,
        "all_options": available_options,
        "recommendation": f"Use {recommended['mode']} shipping for {recommended['transit_days']} day transit at {recommended['cost_factor']}x base cost"
    })


@tool
def generate_purchase_order(product_id: str, quantity: int, supplier_id: str) -> str:
    """
    Generate a purchase order recommendation.
    
    Args:
        product_id: The product to order
        quantity: Quantity to order
        supplier_id: The supplier to order from
    
    Returns:
        JSON string with PO details
    """
    product = next((p for p in get_products() if p["id"] == product_id), None)
    supplier = next((s for s in get_suppliers() if s["id"] == supplier_id), None)
    
    if not product or not supplier:
        return json.dumps({"error": "Product or supplier not found"})
    
    po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{product_id[-3:]}"
    total_cost = product["unit_cost"] * quantity
    expected_delivery = (datetime.now() + timedelta(days=product["lead_time_days"])).strftime("%Y-%m-%d")
    
    return json.dumps({
        "po_number": po_number,
        "status": "draft",
        "product": {
            "id": product_id,
            "name": product["name"],
            "unit_cost": product["unit_cost"]
        },
        "supplier": {
            "id": supplier_id,
            "name": supplier["name"],
            "payment_terms": supplier["payment_terms"]
        },
        "quantity": quantity,
        "total_cost": round(total_cost, 2),
        "expected_delivery": expected_delivery,
        "lead_time_days": product["lead_time_days"],
        "action_required": "Review and approve purchase order"
    })


@tool
def get_market_intelligence(topic: str) -> str:
    """
    Get relevant market intelligence and news for supply chain decisions.
    
    Args:
        topic: Topic to search for (e.g., 'semiconductor', 'shipping', 'geopolitical')
    
    Returns:
        JSON string with relevant news and insights
    """
    news = get_news_events()
    
    # Filter news by topic keywords
    relevant_news = []
    for item in news:
        if any(topic.lower() in kw.lower() for kw in item["keywords"]) or topic.lower() in item["headline"].lower():
            relevant_news.append(item)
    
    # If no specific matches, return all news
    if not relevant_news:
        relevant_news = news[:5]
    
    # Analyze sentiment
    positive = len([n for n in relevant_news if n["sentiment"] == "positive"])
    negative = len([n for n in relevant_news if n["sentiment"] == "negative"])
    
    return json.dumps({
        "topic": topic,
        "news_count": len(relevant_news),
        "sentiment_summary": {
            "positive": positive,
            "negative": negative,
            "overall": "positive" if positive > negative else "negative" if negative > positive else "neutral"
        },
        "news_items": relevant_news,
        "insight": f"Found {len(relevant_news)} relevant news items. Overall market sentiment is {'favorable' if positive > negative else 'concerning' if negative > positive else 'mixed'}."
    })


# ============================================================
# LANGCHAIN AGENT DEFINITIONS
# ============================================================

# Define all tools
DEMAND_TOOLS = [forecast_demand, analyze_stockout_risk]
INVENTORY_TOOLS = [calculate_reorder_point, check_warehouse_levels]
SUPPLIER_TOOLS = [score_supplier_risk, get_shipping_options, get_market_intelligence]
ACTION_TOOLS = [generate_purchase_order]

ALL_TOOLS = DEMAND_TOOLS + INVENTORY_TOOLS + SUPPLIER_TOOLS + ACTION_TOOLS


class SupplyChainAgentSystem:
    """
    LangChain-based multi-agent system for supply chain intelligence.
    Uses LangGraph for agent orchestration and coordination.
    """
    
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_host = ollama_host
        self.model = model
        self.llm = None
        self.tools = ALL_TOOLS
        self.agent_prompts = self._create_agent_prompts()
        
        # Initialize LLM
        try:
            self.llm = ChatOllama(
                base_url=ollama_host,
                model=model,
                temperature=0.3
            )
            logger.info(f"LangChain ChatOllama initialized with model {model}")
        except Exception as e:
            logger.warning(f"Could not initialize Ollama: {e}. Using mock mode.")
            self.llm = None
    
    def _create_agent_prompts(self) -> Dict[str, str]:
        """Create system prompts for each agent"""
        return {
            "orchestrator": """You are the Orchestrator Agent for SupplyMind, an AI-powered supply chain operating system.

Your role is to:
1. Analyze incoming tasks and determine which specialized agents should handle them
2. Coordinate between Demand, Inventory, Supplier, and Action agents
3. Synthesize results from multiple agents into coherent recommendations
4. Make final decisions based on agent outputs

When analyzing a task:
- Identify the key supply chain domain (demand, inventory, supplier, logistics)
- Determine which tools are needed
- Consider cross-functional impacts
- Provide clear, actionable recommendations

Always respond with structured analysis including:
- Task understanding
- Agents involved
- Key findings
- Recommended actions""",
            
            "demand": """You are the Demand Agent for SupplyMind.

Your expertise includes:
- Demand forecasting using historical data and trends
- Stockout risk prediction and prevention
- Demand anomaly detection
- Seasonal pattern recognition

Available tools:
- forecast_demand: Predict future demand for products
- analyze_stockout_risk: Assess risk of running out of stock

When analyzing demand:
- Consider historical patterns
- Account for seasonality
- Identify trends
- Quantify uncertainty with confidence intervals

Provide data-driven insights with specific numbers and recommendations.""",
            
            "inventory": """You are the Inventory Agent for SupplyMind.

Your expertise includes:
- Inventory optimization and reorder point calculation
- Safety stock determination
- Warehouse capacity management
- Working capital optimization

Available tools:
- calculate_reorder_point: Determine optimal reorder levels
- check_warehouse_levels: Analyze warehouse inventory health

When analyzing inventory:
- Balance service levels with carrying costs
- Consider lead times and demand variability
- Identify slow-moving and obsolete inventory
- Recommend optimal stock levels

Provide specific reorder recommendations with quantities and timing.""",
            
            "supplier": """You are the Supplier Agent for SupplyMind.

Your expertise includes:
- Supplier risk assessment and monitoring
- Vendor performance evaluation
- Shipping mode optimization
- Market intelligence analysis

Available tools:
- score_supplier_risk: Calculate comprehensive supplier risk scores
- get_shipping_options: Recommend optimal shipping modes
- get_market_intelligence: Gather relevant market news and insights

When analyzing suppliers:
- Evaluate performance across quality, delivery, and cost
- Assess financial and geopolitical risks
- Monitor market conditions affecting supply
- Recommend risk mitigation strategies

Provide risk scores with specific factors and actionable recommendations.""",
            
            "action": """You are the Action Agent for SupplyMind.

Your role is to:
- Execute decisions made by other agents
- Generate purchase orders
- Create alerts and notifications
- Log all decisions for audit

Available tools:
- generate_purchase_order: Create PO recommendations

When taking action:
- Verify all parameters before execution
- Document rationale for each action
- Ensure proper approvals are in place
- Track outcomes for continuous improvement

Provide clear action items with specific details and next steps."""
        }
    
    async def invoke_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Invoke a specific tool and return results"""
        tool_map = {t.name: t for t in self.tools}
        
        if tool_name not in tool_map:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            result = tool_map[tool_name].invoke(kwargs)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}
    
    async def run_agent(self, agent_name: str, task: str, context: Dict = None) -> Dict[str, Any]:
        """Run a specific agent with a task"""
        if agent_name not in self.agent_prompts:
            return {"error": f"Agent {agent_name} not found"}
        
        system_prompt = self.agent_prompts[agent_name]
        
        # Build context string
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        user_message = f"""
Task: {task}

Context:
{context_str}

Please analyze this task and provide your expert assessment. Use the available tools if needed.
Respond with a JSON object containing:
- analysis: Your detailed analysis
- recommendations: List of specific recommendations
- tools_to_use: List of tools you would use (tool_name and parameters)
- confidence: Your confidence level (0-1)
"""
        
        if self.llm:
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
                
                response = await self.llm.ainvoke(messages)
                
                # Try to parse as JSON
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {
                        "analysis": response.content,
                        "recommendations": [],
                        "raw_response": True
                    }
            except Exception as e:
                logger.error(f"LLM invocation failed: {e}")
                return self._get_mock_agent_response(agent_name, task, context)
        else:
            return self._get_mock_agent_response(agent_name, task, context)
    
    def _get_mock_agent_response(self, agent_name: str, task: str, context: Dict = None) -> Dict[str, Any]:
        """Generate mock response when LLM is unavailable"""
        task_lower = task.lower()
        
        if agent_name == "orchestrator":
            agents_needed = []
            if any(kw in task_lower for kw in ["demand", "forecast", "predict"]):
                agents_needed.append("demand")
            if any(kw in task_lower for kw in ["inventory", "stock", "warehouse"]):
                agents_needed.append("inventory")
            if any(kw in task_lower for kw in ["supplier", "vendor", "risk"]):
                agents_needed.append("supplier")
            if any(kw in task_lower for kw in ["order", "purchase", "action"]):
                agents_needed.append("action")
            
            return {
                "analysis": f"Analyzed task: '{task}'. This requires coordination across multiple supply chain domains.",
                "agents_involved": agents_needed or ["demand", "inventory"],
                "recommendations": [
                    "Gather data from relevant agents",
                    "Cross-reference findings for holistic view",
                    "Prioritize actions based on risk and impact"
                ],
                "execution_plan": f"Will coordinate with {', '.join(agents_needed)} agents",
                "confidence": 0.85
            }
        
        elif agent_name == "demand":
            return {
                "analysis": "Demand analysis indicates seasonal patterns with upward trend. Historical MAPE of 8.5% suggests reliable forecasting.",
                "recommendations": [
                    "Increase safety stock for Q4 peak season",
                    "Monitor promotional impact on demand",
                    "Consider demand sensing for short-term adjustments"
                ],
                "forecast_summary": {
                    "trend": "increasing",
                    "seasonality": "detected",
                    "volatility": "moderate"
                },
                "confidence": 0.82
            }
        
        elif agent_name == "inventory":
            return {
                "analysis": "Inventory health check reveals 3 critical items requiring immediate attention. Overall warehouse utilization at 74%.",
                "recommendations": [
                    "Expedite orders for critical items",
                    "Review reorder points for high-velocity SKUs",
                    "Consider cross-docking for slow movers"
                ],
                "inventory_health": {
                    "critical_items": 3,
                    "optimal_items": 25,
                    "overstock_items": 5
                },
                "confidence": 0.88
            }
        
        elif agent_name == "supplier":
            return {
                "analysis": "Supplier risk assessment shows elevated risk for Asia Pacific suppliers due to geopolitical tensions. Quality scores remain strong.",
                "recommendations": [
                    "Diversify supplier base for critical components",
                    "Increase safety stock for single-source items",
                    "Negotiate improved payment terms with low-risk suppliers"
                ],
                "risk_summary": {
                    "high_risk_suppliers": 2,
                    "medium_risk_suppliers": 3,
                    "low_risk_suppliers": 3
                },
                "confidence": 0.79
            }
        
        elif agent_name == "action":
            return {
                "analysis": "Action plan generated based on agent recommendations. 3 purchase orders ready for approval.",
                "recommendations": [
                    "Approve high-priority POs immediately",
                    "Schedule routine orders for batch processing",
                    "Alert stakeholders of critical actions"
                ],
                "pending_actions": [
                    {"type": "purchase_order", "priority": "high", "value": 45000},
                    {"type": "alert", "priority": "medium", "recipients": 3},
                    {"type": "report", "priority": "low", "scheduled": True}
                ],
                "confidence": 0.92
            }
        
        return {"error": "Unknown agent", "agent": agent_name}
    
    async def orchestrate(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """
        Main orchestration method - coordinates multiple agents to complete a task.
        This is the entry point for multi-agent processing.
        """
        result = {
            "task": task,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_outputs": {},
            "tools_used": [],
            "final_response": None
        }
        
        # Step 1: Orchestrator analyzes the task
        orchestrator_response = await self.run_agent("orchestrator", task, context)
        result["agent_outputs"]["orchestrator"] = orchestrator_response
        
        # Step 2: Determine which agents to involve
        agents_to_run = orchestrator_response.get("agents_involved", [])
        
        # Step 3: Run relevant specialized agents
        for agent in agents_to_run:
            if agent in ["demand", "inventory", "supplier", "action"]:
                agent_response = await self.run_agent(agent, task, context)
                result["agent_outputs"][agent] = agent_response
        
        # Step 4: Synthesize final response
        all_recommendations = []
        for agent_name, output in result["agent_outputs"].items():
            if isinstance(output, dict) and "recommendations" in output:
                all_recommendations.extend(output["recommendations"])
        
        result["final_response"] = {
            "summary": f"Task '{task}' processed by {len(result['agent_outputs'])} agents",
            "agents_consulted": list(result["agent_outputs"].keys()),
            "consolidated_recommendations": all_recommendations[:10],
            "status": "completed"
        }
        
        return result


# Global instance
from datetime import timedelta
agent_system = SupplyChainAgentSystem()
