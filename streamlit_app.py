"""
AI Operations Assistant - Premium Streamlit UI

A high-end, glassmorphism-styled web interface for the multi-agent AI system.
Features:
- Real-time agent workflow visualization
- Animated status indicators
- Rich data rendering (charts, news cards, repo widgets)
- Glassmorphism design system
"""
import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Ops Assistant | Enterprise",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start collapsed for more screen real estate
)

# --- 🎨 DESIGN SYSTEM & CSS ----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* BASE THEME */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(18, 18, 28) 0%, rgb(10, 10, 15) 90%);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }

    /* GLASSMORPHISM CARD */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.3);
    }

    /* AGENT INDICATORS */
    .agent-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 50px;
        font-size: 0.85em;
        font-weight: 600;
        margin-right: 10px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px currentColor;
    }

    /* INPUT FIELD */
    .stTextArea textarea {
        background: rgba(20, 20, 30, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e0e0e0 !important;
        font-size: 1.1em !important;
        transition: all 0.3s !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        font-size: 0.9em;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
    }

    /* METRICS */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* CUSTOM GRID FOR RESULTS */
    .result-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
    }

    /* WEATHER CARD */
    .weather-widget {
        background: linear-gradient(135deg, #3b82f620 0%, #1d4ed820 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }

    /* NEWS CARD */
    .news-item {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid #f59e0b;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 0 12px 12px 0;
    }

    /* CODE BLOCKS */
    code {
        color: #f472b6 !important;
        background: rgba(244, 114, 182, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 CONFIG & UTILS --------------------------------------------------------
API_URL = st.sidebar.text_input("API Endpoint", value="http://localhost:8000")

def get_status_color(status):
    return "#10b981" if status == "success" else "#ef4444"

def make_request(method, endpoint, **kwargs):
    try:
        if method == "GET":
            resp = requests.get(f"{API_URL}{endpoint}", **kwargs)
        else:
            resp = requests.post(f"{API_URL}{endpoint}", **kwargs)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# --- 📊 VISUALIZATION COMPONENTS ----------------------------------------------
def render_weather_chart(data):
    """Render weather data using Plotly if structure allows"""
    # Just a placeholder for advanced viz if data structure matched
    pass

def render_news_grid(articles):
    """Render news articles in a responsive grid"""
    cols = st.columns(2)
    for i, article in enumerate(articles):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="news-item">
                <h4><a href="{article.get('url', '#')}" style="color:#e0e0e0;text-decoration:none" target="_blank">{article.get('title')}</a></h4>
                <p style="color:#9ca3af;font-size:0.9em">{article.get('description', '')[:100]}...</p>
                <div style="font-size:0.8em;color:#6b7280;margin-top:10px">
                    <span>📰 {article.get('source')}</span> • <span>🕒 {article.get('published_at', '')[:10]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- 📱 MAIN APP LAYOUT -------------------------------------------------------

# Header Section
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("https://img.icons8.com/3d-fluency/94/robot-2.png", width=84)
with col_title:
    st.markdown("""
        <h1 style='margin-bottom:0'>AI Operations Assistant <span style="font-size:0.5em;vertical-align:top;background:#3b82f6;padding:2px 8px;border-radius:10px;color:white">PRO</span></h1>
        <p style='color:#94a3b8; font-size: 1.1em'>Multi-Agent Orchestration • LangGraph • Redis Caching</p>
    """, unsafe_allow_html=True)

st.write("") # Spacer

# Main Interactive Area
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # Input Area with "Glow" effect
    task_input = st.text_area(
        "Enter your complex task:", 
        height=100, 
        placeholder="e.g., 'Find the top 5 trending AI repos on GitHub, verify their activity, and check if there's any recent news about them.'",
        label_visibility="collapsed"
    )
    
    col_act, col_opt = st.columns([1, 3])
    with col_act:
        run_btn = st.button("⚡ EXECUTE MISSION", use_container_width=True)
    with col_opt:
        st.markdown("""
            <div style="display:flex; gap:15px; margin-top:10px; color:#64748b; font-size:0.9em">
                <span>⚡ Parallel Execution Active</span>
                <span>🔥 Redis Caching Enabled</span>
                <span>🛡️ Auto-Verification On</span>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🚀 EXECUTION LOGIC -------------------------------------------------------
if run_btn and task_input:
    start_time = time.time()
    
    # 1. State Visualization Container
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    # Placeholder for live thinking steps
    with status_container.container():
        st.info("🧠 **Planner Agent** is thinking...")
    
    # API Call
    result = make_request("POST", "/process", json={"task": task_input}, timeout=120)
    
    duration = time.time() - start_time
    progress_bar.progress(100)
    status_container.empty() # Clear initial loader
    
    if result.get("error"):
        st.error(f"❌ Mission Failed: {result['error']}")
    else:
        # --- 🏁 RESULTS DASHBOARD ---------------------------------------------
        
        # 1. Top Level Metrics
        st.markdown("### 📊 Mission Report")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Status", "Success" if result.get("success") else "Partial", delta="Completed")
        m_col2.metric("Time", f"{duration:.2f}s", delta_color="off")
        m_col3.metric("Steps Executed", len(result.get("plan", {}).get("steps", [])), "LangGraph")
        m_col4.metric("Est. Cost", f"${result.get('cost', 0):.5f}", "-Low")
        
        # 2. Key Findings (The "Response")
        response = result.get("response", {})
        summary = response.get("summary", "No summary provided.")
        
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #10b981; background: rgba(16, 185, 129, 0.05);">
            <h3 style="color:#10b981; margin-top:0">💡 Executive Summary</h3>
            <p style="font-size: 1.1em; line-height: 1.6; color: #e2e8f0">{summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Rich Data Visualization
        data = response.get("data", {})
        if data:
            st.subheader("📦 Verified Intelligence")
            
            # Smart rendering based on keys
            weather_data = data.get("weather", [])
            news_data = data.get("news", [])
            github_data = data.get("github", [])
            
            # --- WEATHER WIDGET ---
            if weather_data and isinstance(weather_data, list):
                w_cols = st.columns(len(weather_data))
                for idx, w in enumerate(weather_data):
                    with w_cols[idx]:
                         st.markdown(f"""
                            <div class="weather-widget">
                                <h3>{w.get('city', 'Unknown')}</h3>
                                <div style="font-size:2.5em; font-weight:bold">{w.get('temperature', '?')}°</div>
                                <div>{w.get('conditions', 'Clear')}</div>
                                <div style="font-size:0.8em; opacity:0.7; margin-top:5px">
                                    💧 {w.get('humidity', '?')}% | 💨 {w.get('wind_speed', '?')} km/h
                                </div>
                            </div>
                         """, unsafe_allow_html=True)
            
            # --- NEWS GRID ---
            if news_data and isinstance(news_data, dict):
                articles = news_data.get("articles", [])
                if articles:
                    st.markdown("#### 📰 Relevant News")
                    render_news_grid(articles)
            
            # --- OTHER DATA (Fallback) ---
            with st.expander("🔍 View Raw Structured Data"):
                st.json(data)

        # 4. Technical Breakdown (Tabs)
        st.write("")
        st.subheader("🛠️ Technical Execution Details")
        
        tech_tab1, tech_tab2, tech_tab3 = st.tabs(["🗺️ Execution Plan", "⚡ Agent Logs", "🧾 Source References"])
        
        with tech_tab1:
            plan = result.get("plan", {})
            for step in plan.get("steps", []):
                st.markdown(f"""
                <div class="agent-badge" style="width:100%; display:flex; justify-content:space-between; margin-bottom:8px">
                    <span>
                        <span style="color:#3b82f6; font-weight:bold">#{step.get('step_number')}</span> 
                        {step.get('description')}
                    </span>
                    <span style="font-family:monospace; background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:4px">
                        {step.get('tool')}.{step.get('action')}()
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
        with tech_tab2:
            st.code(json.dumps(result.get("execution", {}), indent=2), language="json")
            
        with tech_tab3:
             sources = response.get("sources", [])
             if sources:
                 for s in sources:
                     st.markdown(f"- 🔗 [{s}]({s})")
             else:
                 st.info("No external sources cited.")

# --- 📊 ANALYTICS SIDEBAR -----------------------------------------------------
with st.sidebar:
    st.header("📈 Live Analytics")
    
    # Health Check
    health = make_request("GET", "/health")
    
    if health and "cache" in health:
        cache = health["cache"]
        
        # Donut Chart for Cache
        hits = cache.get("hits", 0)
        misses = cache.get("misses", 0)
        
        if hits + misses > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Cache Hits', 'API Calls'],
                values=[hits, misses],
                hole=.7,
                marker=dict(colors=['#10b981', '#3b82f6']),
                textinfo='none'
            )])
            fig.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=120,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(text=f"{int(hits/(hits+misses)*100)}%", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            col_k1, col_k2 = st.columns(2)
            col_k1.metric("Hits", hits)
            col_k2.metric("Misses", misses)
        else:
            st.info("No traffic yet.")
    
    st.divider()
    st.caption(f"System Version: {health.get('version', '2.0.0') if health else 'Unknown'}")
    if st.button("🗑️ Flush Redis Cache"):
        make_request("POST", "/cache/clear")
        st.toast("Cache Cleared!", icon="🗑️")

# Footer
st.markdown("""
<br><br>
<div style="text-align: center; opacity: 0.5; font-size: 0.8em">
    AI Operations Assistant • Designed by Antigravity
</div>
""", unsafe_allow_html=True)
