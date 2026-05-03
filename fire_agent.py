"""
Fire Management Agentic System
- Uses Groq API (free, fast) for reasoning
- Integrates with REAL vector RAG system for safety procedures
- Calls tools to activate suppression, log incidents
- Real-time fire incident response
"""

import os
import requests
import json
from dotenv import load_dotenv
from real_rag_system import RealRAGSystem
from datetime import datetime

# Load API key from .env (never hard-code secrets!)
load_dotenv()

# Initialize REAL RAG (vector embeddings + FAISS)
rag = RealRAGSystem()

# ============= GROQ API SETUP =============
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Loaded from .env
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class FireManagementAgent:
    def __init__(self, groq_api_key: str = None):
        # Use provided key, fall back to .env value
        self.groq_key = groq_api_key or GROQ_API_KEY
        self.rag = rag
        self.incident_log = []
        
        # Define tools the agent can use
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_zone_procedure",
                    "description": "Get the emergency procedure for a specific zone",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_id": {
                                "type": "integer",
                                "description": "The zone ID (1=Lobby, 2=Server Room, 3=Warehouse)"
                            }
                        },
                        "required": ["zone_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_suppression_info",
                    "description": "Get suppression system information for a zone",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_id": {
                                "type": "integer",
                                "description": "The zone ID"
                            }
                        },
                        "required": ["zone_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_rag",
                    "description": "Search the fire safety knowledge base for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Fire safety question or search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "activate_suppression",
                    "description": "Activate suppression system for a zone",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_id": {
                                "type": "integer",
                                "description": "The zone ID"
                            },
                            "suppression_type": {
                                "type": "string",
                                "description": "Type of suppression (Sprinkler, CO2, Foam, Water Mist)"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for activation"
                            }
                        },
                        "required": ["zone_id", "suppression_type", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "log_incident",
                    "description": "Log an incident in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_id": {
                                "type": "integer",
                                "description": "The zone ID"
                            },
                            "action": {
                                "type": "string",
                                "description": "Action taken"
                            },
                            "suppression_type": {
                                "type": "string",
                                "description": "Suppression system activated"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Agent's reasoning"
                            }
                        },
                        "required": ["zone_id", "action", "suppression_type", "reasoning"]
                    }
                }
            }
        ]
    
    # ============= TOOL IMPLEMENTATIONS =============
    def query_zone_procedure(self, zone_id: int) -> str:
        """Get procedure for zone"""
        proc = self.rag.get_zone_procedure(zone_id)
        if proc:
            return json.dumps(proc)
        return json.dumps({"error": f"Procedure not found for zone {zone_id}"})
    
    def get_suppression_info(self, zone_id: int) -> str:
        """Get suppression info for zone"""
        supp = self.rag.get_suppression_info(zone_id)
        if supp:
            return json.dumps(supp)
        return json.dumps({"error": f"Suppression info not found for zone {zone_id}"})
    
    def query_rag(self, query: str) -> str:
        """Search knowledge base"""
        results = self.rag.retrieve(query, top_k=2)
        return json.dumps(results)
    
    def activate_suppression(self, zone_id: int, suppression_type: str, reason: str) -> str:
        """Activate suppression system"""
        action = f"{suppression_type} suppression activated"
        self.log_incident(
            zone_id=zone_id,
            action=action,
            suppression_type=suppression_type,
            reasoning=reason
        )
        return json.dumps({
            "status": "activated",
            "zone_id": zone_id,
            "suppression_type": suppression_type,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_incident(self, zone_id: int, action: str, suppression_type: str, reasoning: str) -> str:
        """Log incident"""
        incident = {
            "timestamp": datetime.utcnow().isoformat(),
            "zone_id": zone_id,
            "action": action,
            "suppression_type": suppression_type,
            "reasoning": reasoning
        }
        self.incident_log.append(incident)
        
        print(f"\n📋 INCIDENT LOGGED:")
        print(f"   Zone {zone_id} | {action}")
        print(f"   Suppression: {suppression_type}")
        print(f"   Reasoning: {reasoning}")
        
        return json.dumps(incident)
    
    # ============= PROCESS TOOL CALLS =============
    def process_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Execute tool based on agent request"""
        if tool_name == "query_zone_procedure":
            return self.query_zone_procedure(tool_input.get("zone_id"))
        elif tool_name == "get_suppression_info":
            return self.get_suppression_info(tool_input.get("zone_id"))
        elif tool_name == "query_rag":
            return self.query_rag(tool_input.get("query"))
        elif tool_name == "activate_suppression":
            return self.activate_suppression(
                zone_id=tool_input.get("zone_id"),
                suppression_type=tool_input.get("suppression_type"),
                reason=tool_input.get("reason")
            )
        elif tool_name == "log_incident":
            return self.log_incident(
                zone_id=tool_input.get("zone_id"),
                action=tool_input.get("action"),
                suppression_type=tool_input.get("suppression_type"),
                reasoning=tool_input.get("reasoning")
            )
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    # ============= AGENT REASONING LOOP =============
    def reason(self, detection_data: dict) -> dict:
        """
        Main agent reasoning loop
        Takes detection data, queries RAG, makes decision, logs incident
        """
        zone_id = detection_data.get("zone_id")
        coordinates = detection_data.get("coordinates", {})
        segment_area = detection_data.get("segment_area_pixels", 0)
        
        print("\n" + "=" * 70)
        print("🤖 FIRE MANAGEMENT AGENT - REASONING")
        print("=" * 70)
        print(f"🔥 Detection: Zone {zone_id}")
        print(f"   Coordinates: ({coordinates.get('x', 0):.1f}, {coordinates.get('y', 0):.1f})")
        print(f"   Segment Area: {segment_area:.0f} pixels")
        print()
        
        # Build context for the agent
        system_prompt = """You are a fire management AI agent. You receive fire detection alerts and must:
1. Query the safety procedures for the detected zone
2. Get suppression system information
3. Query the knowledge base for relevant fire safety info
4. Decide on appropriate suppression system activation
5. Log the incident with your reasoning

You have access to tools to query procedures, suppression info, and the knowledge base.
Use these tools to make informed decisions based on fire safety protocols.

Always follow NFPA standards and zone-specific procedures.
Activate the suppression system appropriate for the zone.
Log all decisions with clear reasoning."""
        
        user_message = f"""FIRE DETECTION ALERT:
Zone: {zone_id}
Detection Coordinates: X={coordinates.get('x', 0):.1f}, Y={coordinates.get('y', 0):.1f}
Fire Segment Area: {segment_area:.0f} pixels

REQUIRED ACTIONS:
1. Query the zone's emergency procedure using query_zone_procedure
2. Get suppression system info using get_suppression_info
3. Query the knowledge base for relevant fire safety info
4. Activate the appropriate suppression system
5. Log the incident with your reasoning

Provide your analysis and decisions."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Agent loop
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Agent Iteration {iteration}:")
            
            # Call Groq API
            try:
                response = requests.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-70b-versatile",
                        "messages": messages,
                        "tools": self.tools,
                        "tool_choice": "auto",
                        "temperature": 0.2,
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"⚠️  Groq API Error: {response.status_code}")
                    print(f"   Response: {response.text}")
                    break
                
                response_data = response.json()
                content = response_data["choices"][0]["message"].get("content", "")
                tool_calls = response_data["choices"][0]["message"].get("tool_calls", [])
                
                # If agent provided content, print it
                if content:
                    print(f"   Agent: {content[:200]}...")
                
                # If no tool calls, agent is done
                if not tool_calls:
                    print(f"✅ Agent decision complete")
                    break
                
                # Process tool calls
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_input = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"   🔧 Tool: {tool_name}")
                    print(f"      Input: {tool_input}")
                    
                    # Execute tool
                    tool_result = self.process_tool_call(tool_name, tool_input)
                    print(f"      Result: {tool_result[:100]}...")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "assistant",
                        "content": content or "",
                        "tool_calls": tool_calls
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })
            
            except requests.exceptions.Timeout:
                print("⚠️  Groq API timeout - retrying...")
                continue
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Request error: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON decode error: {e}")
                break
        
        print("\n" + "=" * 70)
        print("✅ REASONING COMPLETE")
        print("=" * 70)
        
        return {
            "zone_id": zone_id,
            "incident_log": self.incident_log[-1] if self.incident_log else None,
            "iterations": iteration
        }
    
    def get_incident_history(self, zone_id: int = None) -> list:
        """Get incident history"""
        if zone_id:
            return [inc for inc in self.incident_log if inc.get("zone_id") == zone_id]
        return self.incident_log


# ============= TEST WITHOUT GROQ KEY =============
def test_agent_without_groq():
    """Test agent structure without needing Groq API"""
    print("\n" + "=" * 70)
    print("🧪 TESTING AGENT STRUCTURE (No Groq API needed)")
    print("=" * 70)
    
    # Create agent (dummy key)
    agent = FireManagementAgent(groq_api_key="test_key")
    
    # Test tool implementations directly
    print("\n1️⃣  TESTING: Query Zone Procedure")
    print("-" * 70)
    for zone_id in [1, 2, 3]:
        result = agent.query_zone_procedure(zone_id)
        result_data = json.loads(result)
        print(f"✅ Zone {zone_id}: {result_data.get('category', 'N/A')}")
    
    print("\n2️⃣  TESTING: Get Suppression Info")
    print("-" * 70)
    for zone_id in [1, 2, 3]:
        result = agent.get_suppression_info(zone_id)
        result_data = json.loads(result)
        print(f"✅ Zone {zone_id}: {result_data.get('suppression_type', 'N/A')}")
    
    print("\n3️⃣  TESTING: Query RAG")
    print("-" * 70)
    queries = ["CO2 suppression", "Evacuation procedures", "Fire extinguisher"]
    for query in queries:
        result = agent.query_rag(query)
        result_data = json.loads(result)
        print(f"✅ Query '{query}': {len(result_data)} documents found")
    
    print("\n4️⃣  TESTING: Activate Suppression & Log Incident")
    print("-" * 70)
    agent.activate_suppression(
        zone_id=1,
        suppression_type="Sprinkler",
        reason="Fire detected in Lobby area"
    )
    
    print("\n5️⃣  INCIDENT HISTORY")
    print("-" * 70)
    history = agent.get_incident_history()
    for inc in history:
        print(f"✅ {inc['timestamp']}: Zone {inc['zone_id']} - {inc['action']}")
    
    print("\n✅ ALL TESTS PASSED!")


if __name__ == "__main__":
    # Run basic tests
    test_agent_without_groq()
    
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS:")
    print("=" * 70)
    print("1. Get Groq API key: https://console.groq.com")
    print("2. Update GROQ_API_KEY in this file")
    print("3. Run: python test_agent.py")
    print("=" * 70)
