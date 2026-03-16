#!/usr/bin/env python3
"""
Backend API Testing for SupplyMind - LangChain Multi-Agent Supply Chain System
Tests all backend endpoints and core functionality
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration  
BASE_URL = "https://agentic-supply.preview.emergentagent.com/api"
TIMEOUT = 30

class SupplyMindAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SupplyMind-API-Tester/1.0'
        })
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.results = {}

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
            self.failed_tests.append(f"{test_name}: {details}")
        
        self.results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

    def test_health_endpoint(self) -> bool:
        """Test /health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Health Check", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["status", "ollama_connected", "model", "tools_available", "agents_available"]
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Health Check", False, f"Missing field: {field}")
                    return False
            
            if data["status"] != "healthy":
                self.log_result("Health Check", False, f"Status not healthy: {data['status']}")
                return False
            
            self.log_result("Health Check", True, f"Ollama: {data['ollama_connected']}, Model: {data['model']}, Tools: {data['tools_available']}")
            return True
            
        except Exception as e:
            self.log_result("Health Check", False, str(e))
            return False

    def test_products_endpoint(self) -> bool:
        """Test /products endpoint - should return 10 products"""
        try:
            response = self.session.get(f"{self.base_url}/products", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Products API", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            
            if "products" not in data or "count" not in data:
                self.log_result("Products API", False, "Missing products or count field")
                return False
            
            products = data["products"]
            
            if data["count"] != 10:
                self.log_result("Products API", False, f"Expected 10 products, got {data['count']}")
                return False
            
            if len(products) != 10:
                self.log_result("Products API", False, f"Count mismatch: declared {data['count']}, actual {len(products)}")
                return False
            
            # Validate product structure
            required_fields = ["id", "name", "category", "unit_cost", "lead_time_days"]
            for i, product in enumerate(products):
                for field in required_fields:
                    if field not in product:
                        self.log_result("Products API", False, f"Product {i} missing field: {field}")
                        return False
            
            self.log_result("Products API", True, f"Retrieved {len(products)} products")
            return True
            
        except Exception as e:
            self.log_result("Products API", False, str(e))
            return False

    def test_suppliers_endpoint(self) -> bool:
        """Test /suppliers endpoint - should return 8 suppliers"""
        try:
            response = self.session.get(f"{self.base_url}/suppliers", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Suppliers API", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            
            if "suppliers" not in data or "count" not in data:
                self.log_result("Suppliers API", False, "Missing suppliers or count field")
                return False
            
            suppliers = data["suppliers"]
            
            if data["count"] != 8:
                self.log_result("Suppliers API", False, f"Expected 8 suppliers, got {data['count']}")
                return False
            
            if len(suppliers) != 8:
                self.log_result("Suppliers API", False, f"Count mismatch: declared {data['count']}, actual {len(suppliers)}")
                return False
            
            # Validate supplier structure
            required_fields = ["id", "name", "country", "region", "reliability_score", "quality_rating", "on_time_delivery"]
            for i, supplier in enumerate(suppliers):
                for field in required_fields:
                    if field not in supplier:
                        self.log_result("Suppliers API", False, f"Supplier {i} missing field: {field}")
                        return False
            
            self.log_result("Suppliers API", True, f"Retrieved {len(suppliers)} suppliers")
            return True
            
        except Exception as e:
            self.log_result("Suppliers API", False, str(e))
            return False

    def test_tools_endpoint(self) -> bool:
        """Test /tools endpoint - should return 8 LangChain tools"""
        try:
            response = self.session.get(f"{self.base_url}/tools", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Tools API", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            
            if "tools" not in data or "count" not in data:
                self.log_result("Tools API", False, "Missing tools or count field")
                return False
            
            tools = data["tools"]
            
            if data["count"] != 8:
                self.log_result("Tools API", False, f"Expected 8 tools, got {data['count']}")
                return False
            
            if len(tools) != 8:
                self.log_result("Tools API", False, f"Count mismatch: declared {data['count']}, actual {len(tools)}")
                return False
            
            # Validate tool structure
            required_fields = ["name", "description"]
            for i, tool in enumerate(tools):
                for field in required_fields:
                    if field not in tool:
                        self.log_result("Tools API", False, f"Tool {i} missing field: {field}")
                        return False
            
            self.log_result("Tools API", True, f"Retrieved {len(tools)} LangChain tools")
            return True
            
        except Exception as e:
            self.log_result("Tools API", False, str(e))
            return False

    def test_tools_invoke_forecast(self) -> bool:
        """Test /tools/invoke with forecast_demand tool"""
        try:
            test_data = {
                "tool_name": "forecast_demand",
                "parameters": {
                    "product_id": "PRD-001",
                    "periods": 3
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/tools/invoke",
                json=test_data,
                timeout=TIMEOUT * 2
            )
            
            if response.status_code != 200:
                self.log_result("Tools Invoke (forecast_demand)", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["tool", "result"]
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Tools Invoke (forecast_demand)", False, f"Missing field: {field}")
                    return False
            
            if data["tool"] != "forecast_demand":
                self.log_result("Tools Invoke (forecast_demand)", False, f"Wrong tool returned: {data['tool']}")
                return False
            
            # Check if result contains forecast data
            result = data["result"]
            if isinstance(result, dict) and "product_id" in result and "forecasts" in result:
                self.log_result("Tools Invoke (forecast_demand)", True, f"Forecast generated for {result['product_id']}")
                return True
            else:
                self.log_result("Tools Invoke (forecast_demand)", False, "Invalid forecast result structure")
                return False
            
        except Exception as e:
            self.log_result("Tools Invoke (forecast_demand)", False, str(e))
            return False

    def test_supplier_risk_analysis(self) -> bool:
        """Test /supplier-risk/analyze endpoint - comprehensive analysis"""
        try:
            test_data = {
                "supplier_id": "SUP-001",
                "include_news": True
            }
            
            response = self.session.post(
                f"{self.base_url}/supplier-risk/analyze",
                json=test_data,
                timeout=TIMEOUT * 2  # Give more time for LLM processing
            )
            
            if response.status_code != 200:
                self.log_result("Supplier Risk Analysis", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["supplier_id", "risk_assessment", "agent_insights", "timestamp"]
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Supplier Risk Analysis", False, f"Missing field: {field}")
                    return False
            
            # Validate risk assessment structure
            risk_assessment = data["risk_assessment"]
            if not isinstance(risk_assessment, dict):
                self.log_result("Supplier Risk Analysis", False, "risk_assessment is not a dict")
                return False
            
            risk_required = ["risk_score", "risk_level", "component_scores", "recommendation"]
            for field in risk_required:
                if field not in risk_assessment:
                    self.log_result("Supplier Risk Analysis", False, f"Risk assessment missing: {field}")
                    return False
            
            self.log_result("Supplier Risk Analysis", True, f"Risk: {risk_assessment['risk_level']} ({risk_assessment['risk_score']})")
            return True
            
        except Exception as e:
            self.log_result("Supplier Risk Analysis", False, str(e))
            return False

    def test_analytics_shipments(self) -> bool:
        """Test /analytics/shipments endpoint - should return shipment stats with delay reasons"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/shipments", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Analytics Shipments", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["total_shipments", "on_time", "delayed", "on_time_rate", "delay_reasons"]
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Analytics Shipments", False, f"Missing field: {field}")
                    return False
            
            # Validate delay reasons structure
            delay_reasons = data["delay_reasons"]
            if not isinstance(delay_reasons, dict):
                self.log_result("Analytics Shipments", False, "delay_reasons should be a dict")
                return False
            
            # Check some stats make sense
            total = data["total_shipments"]
            on_time = data["on_time"]
            delayed = data["delayed"]
            
            if total != (on_time + delayed):
                self.log_result("Analytics Shipments", False, f"Shipment counts don't add up: {total} != {on_time} + {delayed}")
                return False
            
            self.log_result("Analytics Shipments", True, f"Total: {total}, On-time: {on_time}, Rate: {data['on_time_rate']}%")
            return True
            
        except Exception as e:
            self.log_result("Analytics Shipments", False, str(e))
            return False

    def test_agent_states_endpoint(self) -> bool:
        """Test /agents/states endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/agents/states", timeout=TIMEOUT)
            
            if response.status_code != 200:
                self.log_result("Agent States", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            
            if "agents" not in data:
                self.log_result("Agent States", False, "Missing agents field")
                return False
            
            agents = data["agents"]
            expected_agents = ["orchestrator", "demand", "inventory", "supplier", "action"]
            
            for agent in expected_agents:
                if agent not in agents:
                    self.log_result("Agent States", False, f"Missing agent: {agent}")
                    return False
                
                agent_data = agents[agent]
                required_fields = ["status"]
                
                for field in required_fields:
                    if field not in agent_data:
                        self.log_result("Agent States", False, f"Agent {agent} missing field: {field}")
                        return False
            
            self.log_result("Agent States", True, f"Retrieved states for {len(agents)} agents")
            return True
            
        except Exception as e:
            self.log_result("Agent States", False, str(e))
            return False

    def test_analytics_endpoints(self) -> bool:
        """Test analytics endpoints"""
        endpoints = [
            "demand-trend",
            "inventory-levels", 
            "supplier-performance",
            "cost-breakdown"
        ]
        
        success_count = 0
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}/analytics/{endpoint}", timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        success_count += 1
                        print(f"✅ Analytics - {endpoint}")
                    else:
                        print(f"❌ Analytics - {endpoint} - Missing data field")
                else:
                    print(f"❌ Analytics - {endpoint} - Status {response.status_code}")
            except Exception as e:
                print(f"❌ Analytics - {endpoint} - {str(e)}")
        
        self.tests_run += len(endpoints)
        self.tests_passed += success_count
        
        return success_count == len(endpoints)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print(f"🔍 Testing SupplyMind LangChain Backend API: {self.base_url}")
        print("=" * 70)
        
        start_time = time.time()
        
        # Core functionality tests
        print("\n📊 Core API Tests:")
        self.test_health_endpoint()
        self.test_products_endpoint()
        self.test_suppliers_endpoint()
        self.test_tools_endpoint()
        self.test_agent_states_endpoint()
        
        print("\n🤖 LangChain Tool Tests:")
        self.test_tools_invoke_forecast()
        self.test_supplier_risk_analysis()
        
        print("\n📈 Analytics Tests:")
        self.test_analytics_endpoints()
        self.test_analytics_shipments()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        print(f"   Execution Time: {execution_time:.2f}s")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": self.tests_passed / self.tests_run * 100,
            "execution_time": execution_time,
            "failed_test_details": self.failed_tests,
            "all_results": self.results
        }

def main():
    """Main test execution"""
    print("🚀 SupplyMind LangChain Backend API Testing Suite")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SupplyMindAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("\n🎉 All tests passed! Backend LangChain system is functioning correctly.")
        return 0
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())