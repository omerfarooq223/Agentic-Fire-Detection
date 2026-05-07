
import os
import json
from fire_agent import FireManagementAgent
from dotenv import load_dotenv

# Load credentials
load_dotenv()

def run_test():
    print("🚀 STARTING EMERGENCY WORKFLOW TEST...")
    
    # Initialize Agent
    agent = FireManagementAgent()
    
    # Simulated Detection Data (Server Room)
    detection_data = {
        "zone_id": 2,  # Server Room
        "coordinates": {"x": 450.5, "y": 320.2},
        "segment_area_pixels": 1250.0 # Significant fire
    }
    
    # Trigger Reasoning Loop
    print("\n[AI REASONING IN PROGRESS...]")
    result = agent.reason(detection_data)
    
    print("\n" + "="*50)
    print("✅ TEST COMPLETE")
    print("="*50)
    
    if result and result.get('incident_log'):
        print(f"Incident Logged: {result['incident_log'].get('action', 'N/A')}")
    else:
        print("⚠️ No incident was logged by the agent (Check API logs above).")
    
    print("Check your email for the alert!")

if __name__ == "__main__":
    run_test()
