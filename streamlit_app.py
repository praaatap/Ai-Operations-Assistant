"""
AI Operations Assistant - Streamlit UI

A beautiful web interface for the multi-agent AI system.
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Operations Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Cards */
    .stCard {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Success box */
    .success-box {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin: 10px 0;
    }
    
    /* Error box */
    .error-box {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin: 10px 0;
    }
    
    /* Info box */
    .info-box {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin: 10px 0;
    }
    
    /* Agent cards */
    .agent-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #3498db;
    }
    
    .agent-card.planner {
        border-left-color: #9b59b6;
    }
    
    .agent-card.executor {
        border-left-color: #e67e22;
    }
    
    .agent-card.verifier {
        border-left-color: #27ae60;
    }
    
    /* Result card */
    .result-card {
        background: rgba(46, 204, 113, 0.1);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    
    /* Step indicator */
    .step-indicator {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #3498db;
        color: white;
        text-align: center;
        line-height: 30px;
        font-weight: bold;
        margin-right: 10px;
    }
    
    /* Animated gradient button */
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
    }
    
    /* Metrics */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #3498db;
    }
    
    .metric-label {
        color: #95a5a6;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = st.sidebar.text_input("API URL", value="http://localhost:8000")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return None

def process_task(task: str):
    """Send task to API for processing"""
    try:
        response = requests.post(
            f"{API_URL}/process",
            json={"task": task},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_plan_only(task: str):
    """Get execution plan without running"""
    try:
        response = requests.post(
            f"{API_URL}/plan",
            json={"task": task},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_cache_stats():
    """Get cache statistics"""
    try:
        response = requests.get(f"{API_URL}/cache/stats", timeout=5)
        return response.json()
    except:
        return None

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-2.png", width=80)
    st.title("⚙️ Settings")
    
    # Health Check
    st.subheader("🏥 System Status")
    health = check_api_health()
    
    if health:
        status = health.get("status", "unknown")
        if status == "healthy":
            st.success("✅ API Connected")
        else:
            st.warning(f"⚠️ {status}")
        
        # Agent status
        agents = health.get("agents", {})
        cols = st.columns(3)
        with cols[0]:
            if agents.get("planner"):
                st.markdown("🟢 **Planner**")
            else:
                st.markdown("🔴 **Planner**")
        with cols[1]:
            if agents.get("executor"):
                st.markdown("🟢 **Executor**")
            else:
                st.markdown("🔴 **Executor**")
        with cols[2]:
            if agents.get("verifier"):
                st.markdown("🟢 **Verifier**")
            else:
                st.markdown("🔴 **Verifier**")
        
        # Cache stats
        cache = health.get("cache", {})
        if cache:
            st.subheader("📊 Cache Stats")
            st.metric("Hit Rate", cache.get("hit_rate", "0%"))
            st.caption(f"Hits: {cache.get('hits', 0)} | Misses: {cache.get('misses', 0)}")
            st.caption(f"Backend: {cache.get('backend', 'unknown')}")
    else:
        st.error("❌ API Not Connected")
        st.caption("Make sure the API is running at the URL above")
    
    st.divider()
    
    # Example prompts
    st.subheader("💡 Example Prompts")
    examples = [
        "Find top 5 Python ML libraries on GitHub",
        "What's the weather in Tokyo?",
        "Get latest AI news headlines",
        "Find trending AI repos and get AI news"
    ]
    
    for example in examples:
        if st.button(example, key=f"ex_{example[:20]}", use_container_width=True):
            st.session_state.task_input = example

# Main content
st.title("🤖 AI Operations Assistant")
st.markdown("*Powered by LangGraph Multi-Agent Architecture*")

# Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Process Task", "📋 Plan Only", "📈 Analytics"])

with tab1:
    st.markdown("### Enter your task")
    st.caption("Ask anything about GitHub repos, weather, or news - I'll plan and execute it!")
    
    # Task input
    task_input = st.text_area(
        "Task",
        value=st.session_state.get("task_input", ""),
        height=100,
        placeholder="e.g., Find the most popular Python machine learning libraries on GitHub and get the weather in San Francisco",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        process_btn = st.button("🚀 Process", type="primary", use_container_width=True)
    with col2:
        dry_run = st.checkbox("Dry Run (Plan Only)", value=False)
    
    if process_btn and task_input:
        with st.spinner("🔄 Processing your request..."):
            start_time = time.time()
            
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress while waiting
            status_text.text("📝 Planner Agent: Analyzing your request...")
            progress_bar.progress(20)
            
            # Make API call
            if dry_run:
                result = get_plan_only(task_input)
            else:
                status_text.text("🔧 Executor Agent: Running tools...")
                progress_bar.progress(50)
                result = process_task(task_input)
            
            status_text.text("✅ Verifier Agent: Validating results...")
            progress_bar.progress(80)
            
            end_time = time.time()
            duration = end_time - start_time
            
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()
        
        # Display results
        st.divider()
        
        if "error" in result and result.get("error"):
            st.markdown(f"""
            <div class="error-box">
                <h4>❌ Error</h4>
                <p>{result.get('error')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            success = result.get("success", False)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", "✅ Success" if success else "⚠️ Partial")
            with col2:
                st.metric("Duration", f"{duration:.2f}s")
            with col3:
                plan = result.get("plan", {})
                steps = plan.get("steps", []) if isinstance(plan, dict) else []
                st.metric("Steps", len(steps))
            with col4:
                execution = result.get("execution", {})
                if execution:
                    failed = execution.get("steps_failed", 0)
                    st.metric("Failed", failed)
            
            st.divider()
            
            # Plan details
            with st.expander("📋 Execution Plan", expanded=True):
                plan = result.get("plan", {})
                if isinstance(plan, dict):
                    st.markdown(f"**Task:** {plan.get('task_summary', 'N/A')}")
                    st.markdown(f"**Expected Output:** {plan.get('expected_output', 'N/A')}")
                    
                    steps = plan.get("steps", [])
                    for step in steps:
                        st.markdown(f"""
                        <div class="agent-card executor">
                            <span class="step-indicator">{step.get('step_number', '?')}</span>
                            <strong>{step.get('description', 'No description')}</strong><br>
                            <small>🔧 Tool: <code>{step.get('tool', 'N/A')}</code> | 
                            Action: <code>{step.get('action', 'N/A')}</code></small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Response
            if not dry_run:
                response = result.get("response", {})
                if response:
                    with st.expander("📊 Results", expanded=True):
                        st.markdown(f"""
                        <div class="result-card">
                            <h4>📝 Summary</h4>
                            <p>{response.get('summary', 'No summary available')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Data section
                        data = response.get("data", {})
                        if data:
                            st.markdown("#### 📦 Data")
                            st.json(data)
                        
                        # Sources
                        sources = response.get("sources", [])
                        if sources:
                            st.markdown(f"**Sources:** {', '.join(sources)}")
                        
                        # Errors
                        errors = response.get("errors", [])
                        if errors:
                            st.warning(f"⚠️ Some errors occurred: {', '.join(errors)}")

with tab2:
    st.markdown("### 📋 Plan Preview")
    st.caption("See what the AI would do without actually executing it")
    
    plan_input = st.text_area(
        "Task for planning",
        height=80,
        placeholder="Enter a task to see the execution plan...",
        key="plan_input"
    )
    
    if st.button("📝 Generate Plan", type="secondary"):
        if plan_input:
            with st.spinner("Generating plan..."):
                result = get_plan_only(plan_input)
            
            if result.get("success"):
                plan = result.get("plan", {})
                st.success("Plan generated successfully!")
                
                st.markdown(f"**Summary:** {plan.get('task_summary', 'N/A')}")
                st.markdown(f"**Expected Output:** {plan.get('expected_output', 'N/A')}")
                
                steps = plan.get("steps", [])
                for i, step in enumerate(steps):
                    with st.container():
                        cols = st.columns([1, 10])
                        with cols[0]:
                            st.markdown(f"### {step.get('step_number', i+1)}")
                        with cols[1]:
                            st.markdown(f"**{step.get('description', 'No description')}**")
                            st.code(f"Tool: {step.get('tool')} | Action: {step.get('action')}")
                            if step.get("parameters"):
                                st.json(step.get("parameters"))
            else:
                st.error(f"Failed: {result.get('error', 'Unknown error')}")

with tab3:
    st.markdown("### 📈 System Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏥 Health Status")
        health = check_api_health()
        if health:
            st.json(health)
        else:
            st.error("Cannot fetch health data")
    
    with col2:
        st.markdown("#### 📊 Cache Performance")
        cache_stats = get_cache_stats()
        if cache_stats:
            st.metric("Backend", cache_stats.get("backend", "unknown").upper())
            
            hits = cache_stats.get("hits", 0)
            misses = cache_stats.get("misses", 0)
            total = hits + misses
            
            if total > 0:
                import plotly.graph_objects as go
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Hits', 'Misses'],
                    values=[hits, misses],
                    hole=.6,
                    marker_colors=['#27ae60', '#e74c3c']
                )])
                fig.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No cache activity yet")
        else:
            st.warning("Cannot fetch cache stats")
    
    # Clear cache button
    if st.button("🗑️ Clear Cache"):
        try:
            response = requests.post(f"{API_URL}/cache/clear", timeout=5)
            if response.status_code == 200:
                st.success("Cache cleared!")
            else:
                st.error("Failed to clear cache")
        except:
            st.error("Cannot connect to API")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #95a5a6; font-size: 0.9em;">
    <p>AI Operations Assistant v2.0.0 | Powered by LangGraph & Redis</p>
    <p>📖 <a href="/docs" target="_blank">API Docs</a> | 
    🔄 <a href="/graph" target="_blank">Workflow Graph</a></p>
</div>
""", unsafe_allow_html=True)
