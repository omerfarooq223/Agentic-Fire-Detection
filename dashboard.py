import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from PIL import Image
import io

# ============================================================
# CONFIGURATION & STYLING
# ============================================================
st.set_page_config(
    page_title="FireWatch AI | Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    div[data-testid="stMetricValue"] {
        color: #ff4b4b;
    }
    .agent-reasoning {
        background-color: #1c2128;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        font-family: 'Courier New', Courier, monospace;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

BACKEND_URL = "http://localhost:8000"

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_data(endpoint):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def update_incident_status(incident_id, status):
    try:
        requests.patch(f"{BACKEND_URL}/api/incidents/{incident_id}/status?status={status}")
        return True
    except:
        return False

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/785/785116.png", width=100)
    st.title("System Control")
    
    backend_status = get_data("/api/health")
    if backend_status:
        st.success("● Backend Online")
    else:
        st.error("○ Backend Offline")
    
    st.divider()
    st.subheader("Quick Settings")
    st.slider("Detection Sensitivity", 0.0, 1.0, 0.45)
    st.checkbox("Auto-deploy Suppression", value=True)
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

# ============================================================
# MAIN DASHBOARD
# ============================================================
st.title("🔥 FireWatch AI — Management Dashboard")
st.caption("Agentic RAG-Driven Fire Detection & Response System")

# --- ROW 1: METRICS ---
summary = get_data("/api/dashboard/summary")
col1, col2, col3, col4 = st.columns(4)

if summary:
    col1.metric("Total Detections", summary.get("total_detections", 0))
    col2.metric("Active Incidents", summary.get("active_incidents", 0))
    col3.metric("Monitored Zones", summary.get("total_zones", 0))
    col4.metric("Last Alert", summary.get("last_detection", "None")[-8:] if summary.get("last_detection") else "N/A")
else:
    st.warning("Could not fetch summary data. Is the backend running?")

st.divider()

# --- ROW 2: LIVE INCIDENT & AGENT REASONING ---
left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("📸 Latest Detection Feed")
    detections = get_data("/api/detections")
    if detections and len(detections) > 0:
        latest = detections[-1]
        img_url = f"{BACKEND_URL}/images/{latest['image_filename']}"
        st.image(img_url, use_container_width=True, caption=f"Zone {latest['zone_id']} | {latest['timestamp']}")
    else:
        st.info("No active detections found.")

with right_col:
    st.subheader("🤖 Agent Reasoning & RAG Insight")
    incidents = get_data("/api/incidents")
    if incidents and len(incidents) > 0:
        latest_inc = incidents[-1]
        st.markdown(f"""
        <div class="agent-reasoning">
            <p><strong>DECISION:</strong> {latest_inc['action_taken']}</p>
            <p><strong>SUPPRESSION:</strong> {latest_inc['sprinkler_type']}</p>
            <hr style="border-color:#30363d">
            <p style="font-size: 0.9rem;">{latest_inc['agent_reasoning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎛️ Manual Overrides")
        b1, b2, b3 = st.columns(3)
        if b1.button("✅ Resolve", key="res"):
            update_incident_status(latest_inc['incident_id'], "resolved")
            st.toast("Incident marked as Resolved")
        if b2.button("🚫 Override", key="over"):
            update_incident_status(latest_inc['incident_id'], "manual_override")
            st.toast("Manual Override Engaged")
        if b3.button("⚠️ Alarm Off", key="alarm"):
            st.toast("External Alarms Silenced")
    else:
        st.info("Waiting for agent activity...")

# --- ROW 3: ANALYTICS & TIMELINE ---
st.divider()
st.subheader("📈 System Analytics")
c1, c2 = st.columns(2)

with c1:
    zone_data = get_data("/api/dashboard/incidents-by-zone")
    if zone_data:
        df = pd.DataFrame(zone_data)
        fig = px.bar(df, x='zone_name', y='incident_count', 
                     title="Incidents by Zone",
                     color='incident_count',
                     color_continuous_scale='Reds')
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

with c2:
    if incidents:
        df_inc = pd.DataFrame(incidents)
        df_inc['timestamp'] = pd.to_datetime(df_inc['timestamp'])
        fig2 = px.scatter(df_inc, x='timestamp', y='sprinkler_type', 
                          color='status', title="Response Timeline",
                          hover_data=['action_taken'])
        fig2.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

# Auto-refresh
time.sleep(5)
st.rerun()
