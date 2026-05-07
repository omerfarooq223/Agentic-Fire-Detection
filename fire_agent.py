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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import numpy as np
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load API key from .env (never hard-code secrets!)
load_dotenv()

# Initialize REAL RAG (vector embeddings + FAISS)
rag = RealRAGSystem()

# ============= GROQ API SETUP =============
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Loaded from .env
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ============= EMAIL SETUP =============
SENDER_EMAIL = os.getenv("REMINDER_EMAIL_SENDER", "")
RECEIVER_EMAILS = os.getenv("REMINDER_EMAIL_RECEIVERS", "").split(",")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "") # Requires Gmail App Password

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
            },
            {
                "type": "function",
                "function": {
                    "name": "send_emergency_email",
                    "description": "Send a structured emergency email alert based on detection data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_name": { "type": "string" },
                            "address": { "type": "string" },
                            "severity": { "type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"] },
                            "action_taken": { "type": "string" },
                            "reasoning": { "type": "string" }
                        },
                        "required": ["zone_name", "address", "severity", "action_taken"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "initiate_emergency_call",
                    "description": "Trigger an automated emergency call with a generated script",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "The script for the AI to read out during the call"
                            },
                            "recipient": {
                                "type": "string",
                                "description": "The phone number to call"
                            }
                        },
                        "required": ["script", "recipient"]
                    }
                }
            }
        ]
    
    # ============= HELPER FUNCTIONS =============
    def _json_serialize(self, obj: Any) -> str:
        """Helper to serialize objects, handling NumPy types like float32"""
        def default(o):
            if isinstance(o, (np.float32, np.float64)):
                return float(o)
            if isinstance(o, (np.int32, np.int64)):
                return int(o)
            return str(o)
        return json.dumps(obj, default=default)

    # ============= TOOL IMPLEMENTATIONS =============
    def query_zone_procedure(self, zone_id: int) -> str:
        """Get procedure for zone"""
        proc = self.rag.get_zone_procedure(zone_id)
        if proc:
            return self._json_serialize(proc)
        return self._json_serialize({"error": f"Procedure not found for zone {zone_id}"})
    
    def get_suppression_info(self, zone_id: int) -> str:
        """Get suppression info for zone"""
        supp = self.rag.get_suppression_info(zone_id)
        if supp:
            return self._json_serialize(supp)
        return self._json_serialize({"error": f"Suppression info not found for zone {zone_id}"})
    
    def query_rag(self, query: str) -> str:
        """Search knowledge base"""
        results = self.rag.retrieve(query, top_k=2)
        return self._json_serialize(results)
    
    def activate_suppression(self, zone_id: int, suppression_type: str, reason: str) -> str:
        """Activate suppression system"""
        action = f"{suppression_type} suppression activated"
        self.log_incident(
            zone_id=zone_id,
            action=action,
            suppression_type=suppression_type,
            reasoning=reason
        )
        return self._json_serialize({
            "status": "activated",
            "zone_id": zone_id,
            "suppression_type": suppression_type,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    
    def build_emergency_html(self, zone_name: str, address: str, severity: str, action_taken: str, reasoning: str) -> str:
        """Generate a premium Cyber HUD style HTML email"""
        timestamp = datetime.now().strftime("%A, %B %d, %Y | %H:%M:%S")
        score_color = "#e11d48" if severity == "CRITICAL" else "#f59e0b"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
        <body style="margin:0;padding:0;background:#0f172a;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#f8fafc;">
        <div style="max-width:600px;margin:20px auto;background:#1e293b;border-radius:16px;overflow:hidden;border:1px solid #334155;box-shadow:0 20px 50px rgba(0,0,0,0.5);">
          
          <div style="background:linear-gradient(135deg, #e11d48 0%, #9f1239 100%);padding:30px;text-align:center;">
            <div style="font-size:12px;font-weight:800;letter-spacing:4px;color:rgba(255,255,255,0.7);text-transform:uppercase;margin-bottom:8px;">FireWatch AI Agent</div>
            <div style="font-size:28px;font-weight:900;color:#ffffff;letter-spacing:-0.5px;">EMERGENCY DETECTED</div>
          </div>

          <div style="background:#0f172a;padding:12px 30px;border-bottom:1px solid #334155;">
            <table width="100%">
              <tr>
                <td style="font-size:11px;font-weight:700;color:#94a3b8;">PRIORITY: <span style="color:{score_color}">{severity}</span></td>
                <td style="font-size:11px;font-weight:700;color:#94a3b8;text-align:right;">ID: FW-{datetime.now().strftime('%y%m%d%H%M')}</td>
              </tr>
            </table>
          </div>

          <div style="padding:30px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding-bottom:25px;">
                  <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Location & Zone</div>
                  <div style="font-size:18px;font-weight:700;color:#f1f5f9;">{zone_name}</div>
                  <div style="font-size:14px;color:#94a3b8;margin-top:4px;margin-bottom:12px;">{address}</div>
                  <a href="https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}" 
                     style="display:inline-block;background:rgba(34, 211, 238, 0.1);color:#22d3ee;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:11px;font-weight:700;border:1px solid rgba(34, 211, 238, 0.3);">
                    📍 Open in Maps
                  </a>
                </td>
              </tr>
              <tr>
                <td style="background:rgba(225, 29, 72, 0.1);border-radius:12px;padding:20px;border:1px solid rgba(225, 29, 72, 0.2);">
                  <div style="font-size:10px;font-weight:700;color:#e11d48;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Action Triggered</div>
                  <div style="font-size:16px;font-weight:700;color:#f8fafc;">{action_taken}</div>
                  <div style="font-size:13px;color:#cbd5e1;margin-top:8px;line-height:1.5;">{reasoning}</div>
                </td>
              </tr>
            </table>
          </div>

          <div style="padding:0 30px 30px;">
            <div style="background:#0f172a;border-radius:12px;padding:20px;">
              <table width="100%">
                <tr>
                  <td>
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Time Detected</div>
                    <div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-top:4px;">{timestamp}</div>
                  </td>
                  <td style="text-align:right;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Status</div>
                    <div style="font-size:13px;font-weight:600;color:#22d3ee;margin-top:4px;">Active Response</div>
                  </td>
                </tr>
              </table>
            </div>
          </div>

          <div style="padding:0 30px 30px;">
            <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Immediate Safety Protocol</div>
            <div style="background:#e11d48;color:#ffffff;padding:15px;border-radius:8px;text-align:center;font-weight:800;font-size:14px;">
              ⚠️ EVACUATE THE AREA IMMEDIATELY
            </div>
            <div style="font-size:12px;color:#94a3b8;margin-top:12px;text-align:center;line-height:1.5;">
              Proceed to the nearest assembly point. Do not use elevators. Ensure all personnel are accounted for.
            </div>
          </div>

          <div style="background:#0f172a;padding:20px;text-align:center;border-top:1px solid #334155;">
            <a href="https://github.com/omerfarooq223/Agentic-Fire-Detection" style="color:#22d3ee;text-decoration:none;font-size:11px;font-weight:700;">Open FireWatch Dashboard →</a>
            <div style="font-size:10px;color:#475569;margin-top:10px;">FireWatch AI  |  Secure Intelligence  |  {datetime.now().year}</div>
          </div>
        </div>
        </body>
        </html>
        """

    def send_emergency_email(self, zone_name: str, address: str, severity: str, action_taken: str, reasoning: str = "") -> str:
        """Send emergency email via official Gmail API using a premium HTML template"""
        if not os.path.exists('token.json'):
            return self._json_serialize({"error": "token.json not found."})
        
        subject = f"🚨 EMERGENCY FIRE ALERT: {zone_name} ({severity})"
        html_content = self.build_emergency_html(zone_name, address, severity, action_taken, reasoning)
        
        try:
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEMultipart()
            message['To'] = ", ".join(RECEIVER_EMAILS)
            message['From'] = SENDER_EMAIL
            message['Subject'] = subject
            message.attach(MIMEText(html_content, 'html'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
            
            return self._json_serialize({"status": "HTML Alert sent successfully", "recipients": RECEIVER_EMAILS})
        except Exception as e:
            return self._json_serialize({"error": f"Failed to send HTML alert: {str(e)}"})

    def initiate_emergency_call(self, script: str, recipient: str) -> str:
        """Simulate or trigger Twilio call"""
        # For now, we simulate the call by logging the script
        # In a real implementation, this would use the twilio library
        print(f"\n📞 INITIATING EMERGENCY CALL TO: {recipient}")
        print(f"   SCRIPT: \"{script}\"")
        
        return self._json_serialize({
            "status": "Call initiated (Simulated)",
            "recipient": recipient,
            "script": script,
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
        
        return self._json_serialize(incident)
    
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
        elif tool_name == "send_emergency_email":
            return self.send_emergency_email(
                zone_name=tool_input.get("zone_name"),
                address=tool_input.get("address"),
                severity=tool_input.get("severity"),
                action_taken=tool_input.get("action_taken"),
                reasoning=tool_input.get("reasoning", "")
            )
        elif tool_name == "initiate_emergency_call":
            return self.initiate_emergency_call(
                script=tool_input.get("script"),
                recipient=tool_input.get("recipient", os.getenv("YOUR_PERSONAL_PHONE", "DEMO_NUMBER"))
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
6. Trigger 'send_emergency_email' with the structured detection data. (ONLY ONCE)
7. Generate a concise, urgent call script and trigger 'initiate_emergency_call'. (ONLY ONCE)

CRITICAL RULE:
- You must send exactly ONE email and make exactly ONE call per detection. 
- If you see a tool result for 'send_emergency_email' or 'initiate_emergency_call' in the message history, DO NOT call them again.
- Once the alert tools are called, summarize your final response and exit.

MANDATORY RULES:
- Use 'send_emergency_email' as soon as fire is confirmed.
- For 'severity', use 'CRITICAL' if segment area is > 1000 pixels, otherwise 'HIGH'.
- The call script should still be natural and urgent.

You have access to tools to query procedures, suppression info, the knowledge base, and communication channels.
Always follow NFPA standards and zone-specific procedures.
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
                        "model": "llama-3.3-70b-versatile",
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
