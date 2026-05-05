# backend/app/tools/tool_manager.py
"""
Tool Integration Layer - Calculator, Web Search, APIs, etc.
"""
from typing import Dict, Any, List, Optional
import requests
import json
from langchain.tools import tool
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from datetime import datetime
import os


class ToolManager:
    """Manages all integrated tools"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize all available tools"""
        return [
            self._calculator_tool(),
            self._web_search_tool(),
            self._weather_tool(),
            self._code_execution_tool(),
            self._unit_conversion_tool(),
            self._api_call_tool()
        ]
    
    # ============= CALCULATOR =============
    def _calculator_tool(self) -> Tool:
        @tool("calculator")
        def calculator(expression: str) -> str:
            """Safely evaluate mathematical expressions"""
            try:
                # Whitelist allowed operations
                allowed_chars = set('0123456789+-*/(). ')
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        return calculator
    
    # ============= WEB SEARCH =============
    def _web_search_tool(self) -> Tool:
        @tool("web_search")
        def web_search(query: str, num_results: int = 5) -> Dict:
            """Search the web and return results"""
            try:
                # Using Google Custom Search API
                api_key = os.getenv("GOOGLE_API_KEY")
                search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
                
                if not api_key or not search_engine_id:
                    return {"error": "Search API not configured"}
                
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "q": query,
                    "key": api_key,
                    "cx": search_engine_id,
                    "num": num_results
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet")
                    })
                
                return {"query": query, "results": results}
            
            except Exception as e:
                return {"error": str(e)}
        
        return web_search
    
    # ============= WEATHER API =============
    def _weather_tool(self) -> Tool:
        @tool("weather")
        def get_weather(location: str) -> Dict:
            """Get weather information for a location"""
            try:
                api_key = os.getenv("OPENWEATHER_API_KEY")
                if not api_key:
                    return {"error": "Weather API not configured"}
                
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": location,
                    "appid": api_key,
                    "units": "metric"
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if "weather" in data:
                    return {
                        "location": f"{data.get('name')}, {data.get('sys', {}).get('country')}",
                        "temperature": data.get("main", {}).get("temp"),
                        "feels_like": data.get("main", {}).get("feels_like"),
                        "humidity": data.get("main", {}).get("humidity"),
                        "condition": data.get("weather", [{}])[0].get("main"),
                        "description": data.get("weather", [{}])[0].get("description")
                    }
                
                return {"error": data.get("message")}
            
            except Exception as e:
                return {"error": str(e)}
        
        return get_weather
    
    # ============= CODE EXECUTION =============
    def _code_execution_tool(self) -> Tool:
        @tool("execute_code")
        def execute_code(code: str, language: str = "python") -> str:
            """Execute code (with restrictions for safety)"""
            try:
                if language == "python":
                    # Use restricted execution environment
                    restricted_globals = {
                        "__builtins__": {"print": print, "len": len, "range": range}
                    }
                    exec(code, restricted_globals)
                    return "Code executed successfully"
                else:
                    return "Only Python is supported"
            
            except Exception as e:
                return f"Error: {str(e)}"
        
        return execute_code
    
    # ============= UNIT CONVERSION =============
    def _unit_conversion_tool(self) -> Tool:
        @tool("convert_units")
        def convert_units(value: float, from_unit: str, to_unit: str) -> Dict:
            """Convert between units"""
            
            # Temperature conversion
            if from_unit == "C" and to_unit == "F":
                return {"result": (value * 9/5) + 32, "unit": "F"}
            elif from_unit == "F" and to_unit == "C":
                return {"result": (value - 32) * 5/9, "unit": "C"}
            
            # Length conversion
            conversions = {
                ("km", "m"): 1000,
                ("m", "km"): 0.001,
                ("m", "ft"): 3.28084,
                ("ft", "m"): 0.3048,
                ("lb", "kg"): 0.453592,
                ("kg", "lb"): 2.20462,
            }
            
            key = (from_unit, to_unit)
            if key in conversions:
                return {"result": value * conversions[key], "unit": to_unit}
            
            return {"error": f"Conversion {from_unit} to {to_unit} not supported"}
        
        return convert_units
    
    # ============= API CALL TOOL =============
    def _api_call_tool(self) -> Tool:
        @tool("api_call")
        def api_call(url: str, method: str = "GET", headers: Dict = None, 
                     data: Dict = None) -> Dict:
            """Make API calls (with validation)"""
            try:
                # Whitelist safe endpoints
                safe_domains = ["api.github.com", "api.example.com"]
                
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                if domain not in safe_domains:
                    return {"error": "API endpoint not whitelisted"}
                
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                else:
                    return {"error": f"Method {method} not supported"}
                
                return response.json()
            
            except Exception as e:
                return {"error": str(e)}
        
        return api_call
    
    # ============= TOOL SELECTION =============
    def select_tool(self, objective: str) -> Optional[Tool]:
        """Intelligently select tool based on objective"""
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ["calculate", "math", "sum", "multiply"]):
            return next(t for t in self.tools if t.name == "calculator")
        elif any(word in objective_lower for word in ["search", "find", "google", "web"]):
            return next(t for t in self.tools if t.name == "web_search")
        elif any(word in objective_lower for word in ["weather", "temperature"]):
            return next(t for t in self.tools if t.name == "weather")
        elif any(word in objective_lower for word in ["convert", "unit"]):
            return next(t for t in self.tools if t.name == "convert_units")
        elif any(word in objective_lower for word in ["code", "execute", "run", "python"]):
            return next(t for t in self.tools if t.name == "execute_code")
        elif any(word in objective_lower for word in ["api", "call"]):
            return next(t for t in self.tools if t.name == "api_call")
        
        return None
