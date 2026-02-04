"""
AI Operations Assistant - Premium Streamlit UI v2.0

A best-in-class, enterprise-grade web interface for the multi-agent AI system.
Features:
- Real-time agent workflow visualization with animated steps
- Glassmorphism design with dark theme
- Rich data rendering (weather widgets, GitHub repo cards, news feed)
- Live cost & token tracking
- Query history with analytics
- Animated status indicators
- Interactive charts with Plotly
"""
import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import subprocess
import os
from datetime import datetime

# --- 🚀 AUTOMATIC BACKEND LAUNCHER -------------------------------------------
@st.cache_resource
def launch_backend():
    """Checks if the backend is running, if not, launches it."""
    try:
        # Check if backend is already responding
        requests.get("http://localhost:8000/health", timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        # Backend not running, start it
        print("🚀 Starting API Server...")
        # Use subprocess to start uvicorn
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        # Give it a moment to startup
        time.sleep(5)
        return process

# Ensure backend is running
launch_backend()
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Ops Assistant | Enterprise",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0

# --- 🎨 PREMIUM DESIGN SYSTEM & CSS -------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ROOT VARIABLES */
    :root {
        --primary: #6366f1;
        --primary-glow: rgba(99, 102, 241, 0.4);
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.08);
    }

    /* BASE THEME */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide default header */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    /* GLASSMORPHISM CARD */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        margin-bottom: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(99, 102, 241, 0.1);
        transform: translateY(-2px);
    }

    /* HERO SECTION */
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fff 0%, #a5b4fc 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        font-weight: 400;
    }
    
    .pro-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        color: white;
        margin-left: 12px;
        vertical-align: middle;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* AGENT WORKFLOW VISUALIZATION */
    .workflow-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        padding: 30px 0;
        margin: 20px 0;
    }
    
    .agent-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px 30px;
        background: rgba(255, 255, 255, 0.03);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        min-width: 140px;
        transition: all 0.3s ease;
    }
    
    .agent-node.active {
        border-color: #6366f1;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.3);
        transform: scale(1.05);
    }
    
    .agent-node.completed {
        border-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .agent-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    
    .agent-name {
        font-weight: 600;
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    .agent-status {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
    }
    
    .workflow-arrow {
        color: #4b5563;
        font-size: 1.5rem;
    }

    /* INPUT FIELD */
    .stTextArea textarea {
        background: rgba(15, 15, 26, 0.8) !important;
        border: 2px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 16px !important;
        color: #e2e8f0 !important;
        font-size: 1.1rem !important;
        padding: 16px !important;
        transition: all 0.3s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15), 0 0 30px rgba(99, 102, 241, 0.1) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #64748b !important;
    }

    /* PRIMARY BUTTON */
    div.stButton > button[kind="primary"], div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 16px 32px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    div.stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
    }
    
    div.stButton > button:active {
        transform: translateY(-1px);
    }

    /* SECONDARY BUTTON */
    .secondary-btn button {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #e2e8f0 !important;
    }

    /* METRICS CARDS */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* RESULT CARDS */
    .result-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    .success-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.02) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-left: 4px solid #10b981;
    }

    /* WEATHER WIDGET */
    .weather-widget {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
    }
    
    .weather-temp {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .weather-city {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .weather-condition {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .weather-details {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 16px;
        font-size: 0.9rem;
        opacity: 0.8;
    }

    /* GITHUB REPO CARD */
    .repo-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    
    .repo-card:hover {
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    .repo-name {
        color: #60a5fa;
        font-weight: 600;
        font-size: 1.1rem;
        text-decoration: none;
    }
    
    .repo-desc {
        color: #94a3b8;
        font-size: 0.9rem;
        margin: 8px 0;
        line-height: 1.5;
    }
    
    .repo-stats {
        display: flex;
        gap: 16px;
        font-size: 0.85rem;
        color: #64748b;
    }
    
    .repo-stat {
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* NEWS CARD */
    .news-card {
        background: rgba(245, 158, 11, 0.05);
        border-left: 3px solid #f59e0b;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    
    .news-title {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 6px;
        line-height: 1.4;
    }
    
    .news-source {
        color: #64748b;
        font-size: 0.8rem;
    }

    /* STEP INDICATOR */
    .step-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    
    .step-number {
        background: #6366f1;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(0, 0, 0, 0.2);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #94a3b8;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.2) !important;
        color: #a5b4fc !important;
    }

    /* EXPANDER */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 12px !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
    }

    /* ANIMATIONS */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.5); }
        50% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.8); }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    .glow {
        animation: glow 2s ease-in-out infinite;
    }

    /* FOOTER */
    .footer {
        text-align: center;
        padding: 40px 0 20px;
        color: #4b5563;
        font-size: 0.85rem;
    }
    
    .footer a {
        color: #6366f1;
        text-decoration: none;
    }

    /* FEATURE BADGES */
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.8rem;
        color: #94a3b8;
    }
    
    .feature-badge.active {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
        color: #10b981;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 CONFIG & UTILS --------------------------------------------------------
API_URL = "http://localhost:8000"

def make_request(method, endpoint, **kwargs):
    try:
        kwargs.setdefault('timeout', 120)
        if method == "GET":
            resp = requests.get(f"{API_URL}{endpoint}", **kwargs)
        else:
            resp = requests.post(f"{API_URL}{endpoint}", **kwargs)
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API server. Make sure it's running on localhost:8000"}
    except Exception as e:
        return {"error": str(e)}

def render_workflow_visualization(stage="idle"):
    """Render the 3-agent workflow visualization"""
    stages = {
        "idle": {"planner": "", "executor": "", "verifier": ""},
        "planning": {"planner": "active", "executor": "", "verifier": ""},
        "executing": {"planner": "completed", "executor": "active", "verifier": ""},
        "verifying": {"planner": "completed", "executor": "completed", "verifier": "active"},
        "complete": {"planner": "completed", "executor": "completed", "verifier": "completed"},
    }
    s = stages.get(stage, stages["idle"])
    
    st.markdown(f"""
    <div class="workflow-container">
        <div class="agent-node {s['planner']}">
            <div class="agent-icon">🧠</div>
            <div class="agent-name">Planner</div>
            <div class="agent-status">{'✓ Complete' if s['planner'] == 'completed' else '⚡ Active' if s['planner'] == 'active' else 'Waiting'}</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="agent-node {s['executor']}">
            <div class="agent-icon">⚙️</div>
            <div class="agent-name">Executor</div>
            <div class="agent-status">{'✓ Complete' if s['executor'] == 'completed' else '⚡ Active' if s['executor'] == 'active' else 'Waiting'}</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="agent-node {s['verifier']}">
            <div class="agent-icon">✅</div>
            <div class="agent-name">Verifier</div>
            <div class="agent-status">{'✓ Complete' if s['verifier'] == 'completed' else '⚡ Active' if s['verifier'] == 'active' else 'Waiting'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_github_repos(repos):
    """Render GitHub repositories in beautiful cards"""
    for repo in repos:
        st.markdown(f"""
        <div class="repo-card">
            <a href="{repo.get('url', '#')}" target="_blank" class="repo-name">{repo.get('name', 'Unknown')}</a>
            <div class="repo-desc">{repo.get('description', 'No description')[:150]}...</div>
            <div class="repo-stats">
                <span class="repo-stat">⭐ {repo.get('stars', 0):,}</span>
                <span class="repo-stat">🍴 {repo.get('forks', 0):,}</span>
                <span class="repo-stat">💻 {repo.get('language', 'Unknown')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_weather_widget(weather_data):
    """Render weather data in a beautiful widget"""
    location = weather_data.get('location', {})
    weather = weather_data.get('weather', {})
    
    city = location.get('city', weather_data.get('city', 'Unknown'))
    temp = weather.get('temperature', weather_data.get('temperature', '?'))
    condition = weather.get('condition', weather_data.get('condition', 'Clear'))
    humidity = weather.get('humidity', weather_data.get('humidity', '?'))
    wind = weather.get('wind_speed', weather_data.get('wind_speed', '?'))
    
    st.markdown(f"""
    <div class="weather-widget">
        <div class="weather-city">📍 {city}</div>
        <div class="weather-temp">{temp}°</div>
        <div class="weather-condition">{condition}</div>
        <div class="weather-details">
            <span>💧 {humidity}%</span>
            <span>💨 {wind} km/h</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_news_articles(articles):
    """Render news articles"""
    for article in articles[:5]:
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title">{article.get('title', 'No title')}</div>
            <div class="news-source">📰 {article.get('source', 'Unknown')} • {article.get('published_at', '')[:10]}</div>
        </div>
        """, unsafe_allow_html=True)

def render_wikipedia_results(data):
    """Render Wikipedia search results or article summary"""
    if 'article' in data:
        # Single article summary
        article = data['article']
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05)); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 20px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 2rem;">📚</span>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">{article.get('title', 'Unknown')}</div>
                    <div style="font-size: 0.9rem; color: #94a3b8;">{article.get('description', '')}</div>
                </div>
            </div>
            <div style="color: #cbd5e1; line-height: 1.7; font-size: 0.95rem;">{article.get('extract', 'No summary available')[:500]}...</div>
            <a href="{article.get('url', '#')}" target="_blank" style="color: #60a5fa; font-size: 0.9rem; margin-top: 12px; display: inline-block;">Read more on Wikipedia →</a>
        </div>
        """, unsafe_allow_html=True)
    elif 'results' in data:
        # Search results
        for result in data.get('results', [])[:5]:
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px; margin-bottom: 10px;">
                <a href="{result.get('url', '#')}" target="_blank" style="color: #60a5fa; font-weight: 600; text-decoration: none; font-size: 1rem;">📖 {result.get('title', 'Unknown')}</a>
                <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 6px;">{result.get('description', 'No description')[:150]}</div>
            </div>
            """, unsafe_allow_html=True)

def render_jokes(data):
    """Render jokes in fun cards"""
    jokes = data.get('jokes', [])
    for joke in jokes:
        emoji = "😂" if joke.get('category') == 'Programming' else "🤣" if joke.get('category') == 'Dad Joke' else "😄"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.02)); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 20px; margin-bottom: 12px; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">{emoji}</div>
            <div style="color: #e2e8f0; font-size: 1.1rem; line-height: 1.6; font-style: italic;">"{joke.get('joke', 'No joke available')}"</div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 10px;">Category: {joke.get('category', 'General')}</div>
        </div>
        """, unsafe_allow_html=True)

def render_quotes(data):
    """Render quotes in elegant cards"""
    # Handle single quote or multiple quotes
    if 'quote' in data:
        quotes = [data['quote']]
    else:
        quotes = data.get('quotes', [])
    
    for quote in quotes:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.02)); border-left: 4px solid #f59e0b; border-radius: 0 16px 16px 0; padding: 24px; margin-bottom: 12px;">
            <div style="font-size: 2rem; color: #f59e0b; margin-bottom: 8px;">❝</div>
            <div style="color: #e2e8f0; font-size: 1.15rem; line-height: 1.7; font-style: italic; margin-bottom: 12px;">{quote.get('content', 'No quote available')}</div>
            <div style="color: #94a3b8; font-size: 0.95rem; text-align: right;">— {quote.get('author', 'Unknown')}</div>
        </div>
        """, unsafe_allow_html=True)


# --- 📱 MAIN APP LAYOUT -------------------------------------------------------

# Hero Section
st.markdown("""
<div style="text-align: center; padding: 20px 0 40px;">
    <div class="hero-title">
        AI Operations Assistant
        <span class="pro-badge">Enterprise</span>
    </div>
    <div class="hero-subtitle">
        Multi-Agent Orchestration powered by LangGraph • Groq & Gemini LLMs • Real-time API Integration
    </div>
</div>
""", unsafe_allow_html=True)

# Feature Badges - Show available tools
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown('<div class="feature-badge active">🐙 GitHub</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-badge active">🌤️ Weather</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-badge active">📰 News</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="feature-badge active">📚 Wikipedia</div>', unsafe_allow_html=True)
with col5:
    st.markdown('<div class="feature-badge active">😂 Jokes</div>', unsafe_allow_html=True)
with col6:
    st.markdown('<div class="feature-badge active">💬 Quotes</div>', unsafe_allow_html=True)

st.write("")

# Agent Workflow Visualization
st.markdown("### 🔄 Agent Workflow")
workflow_placeholder = st.empty()
with workflow_placeholder.container():
    render_workflow_visualization("idle")

# Main Input Section
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

task_input = st.text_area(
    "Enter your task:",
    height=120,
    placeholder="Try: 'Find top 5 trending AI repositories on GitHub, get the current weather in San Francisco, and fetch the latest technology news headlines.'",
    label_visibility="collapsed"
)

col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
with col_btn1:
    run_btn = st.button("🚀 EXECUTE MISSION", use_container_width=True, type="primary")
with col_btn2:
    example_btn = st.button("📝 Load Example", use_container_width=True)
with col_btn3:
    clear_btn = st.button("🗑️ Clear", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Handle example button
if example_btn:
    st.session_state.example_task = "Find top 3 GitHub repositories for machine learning, get weather in Tokyo and New York, and fetch the latest AI news headlines"
    st.rerun()

if "example_task" in st.session_state:
    task_input = st.session_state.example_task
    del st.session_state.example_task

# --- 🚀 EXECUTION LOGIC -------------------------------------------------------
if run_btn and task_input:
    start_time = time.time()
    
    # Update workflow visualization
    with workflow_placeholder.container():
        render_workflow_visualization("planning")
    
    status_text = st.empty()
    status_text.info("🧠 **Planner Agent** is analyzing your request and creating an execution plan...")
    
    progress_bar = st.progress(0)
    progress_bar.progress(20)
    
    # Make the API call
    result = make_request("POST", "/process", json={"task": task_input})
    
    progress_bar.progress(60)
    with workflow_placeholder.container():
        render_workflow_visualization("executing")
    status_text.info("⚙️ **Executor Agent** is calling external APIs...")
    time.sleep(0.3)
    
    progress_bar.progress(85)
    with workflow_placeholder.container():
        render_workflow_visualization("verifying")
    status_text.info("✅ **Verifier Agent** is validating and formatting results...")
    time.sleep(0.3)
    
    progress_bar.progress(100)
    with workflow_placeholder.container():
        render_workflow_visualization("complete")
    
    duration = time.time() - start_time
    status_text.empty()
    
    if result.get("error"):
        st.error(f"❌ **Mission Failed:** {result['error']}")
    else:
        # Update session state
        st.session_state.total_queries += 1
        st.session_state.total_cost += result.get('cost', 0)
        st.session_state.history.append({
            "task": task_input,
            "time": datetime.now().strftime("%H:%M:%S"),
            "duration": duration,
            "cost": result.get('cost', 0),
            "success": result.get('success', False)
        })
        
        # --- 🏁 RESULTS DASHBOARD ---------------------------------------------
        st.markdown("---")
        st.markdown("## 📊 Mission Results")
        
        # Top Level Metrics
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Status", "✅ Success" if result.get("success") else "⚠️ Partial")
        m_col2.metric("Execution Time", f"{duration:.2f}s")
        m_col3.metric("Steps Executed", result.get("execution", {}).get("steps_executed", 0))
        m_col4.metric("Cost", f"${result.get('cost', 0):.6f}")
        
        st.write("")
        
        # Executive Summary
        response = result.get("response", {})
        summary = response.get("summary", "No summary available.")
        
        st.markdown(f"""
        <div class="glass-card success-card">
            <h3 style="color: #10b981; margin-top: 0;">💡 Executive Summary</h3>
            <p style="font-size: 1.15rem; line-height: 1.7; color: #e2e8f0; margin: 0;">{summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed Results
        data = response.get("data", {})
        execution = result.get("execution", {})
        
        if execution.get("results"):
            st.markdown("### 📦 Detailed Results")
            
            # Create columns for different data types
            result_cols = st.columns(2)
            
            col_idx = 0
            for step_result in execution.get("results", []):
                if step_result.get("status") == "success" and step_result.get("result"):
                    tool = step_result.get("tool", "")
                    result_data = step_result.get("result", {})
                    
                    with result_cols[col_idx % 2]:
                        if tool == "github":
                            st.markdown("#### 🐙 GitHub Repositories")
                            repos = result_data.get("repositories", [])
                            render_github_repos(repos)
                        
                        elif tool == "weather":
                            st.markdown("#### 🌤️ Weather")
                            render_weather_widget(result_data)
                        
                        elif tool == "news":
                            st.markdown("#### 📰 News")
                            articles = result_data.get("articles", [])
                            render_news_articles(articles)
                        
                        elif tool == "wikipedia":
                            st.markdown("#### 📚 Wikipedia")
                            render_wikipedia_results(result_data)
                        
                        elif tool == "jokes":
                            st.markdown("#### 😂 Jokes")
                            render_jokes(result_data)
                        
                        elif tool == "quotes":
                            st.markdown("#### 💬 Quotes")
                            render_quotes(result_data)
                    
                    col_idx += 1
        
        # Technical Details (Expandable)
        with st.expander("🛠️ Technical Execution Details", expanded=False):
            tech_tab1, tech_tab2, tech_tab3 = st.tabs(["📋 Execution Plan", "📊 Step Results", "📝 Raw JSON"])
            
            with tech_tab1:
                plan = result.get("plan", {})
                st.markdown(f"**Task Summary:** {plan.get('task_summary', 'N/A')}")
                st.markdown(f"**Expected Output:** {plan.get('expected_output', 'N/A')}")
                st.markdown("---")
                
                for step in plan.get("steps", []):
                    st.markdown(f"""
                    <div class="step-badge">
                        <span class="step-number">{step.get('step_number')}</span>
                        <span><strong>{step.get('tool')}</strong>.{step.get('action')}() - {step.get('description')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with tech_tab2:
                for step_result in execution.get("results", []):
                    status_icon = "✅" if step_result.get("status") == "success" else "❌"
                    st.markdown(f"""
                    **{status_icon} Step {step_result.get('step_number')}:** {step_result.get('tool')}.{step_result.get('action')}() - {step_result.get('status').upper()}
                    """)
                    if step_result.get("error"):
                        st.error(step_result.get("error"))
            
            with tech_tab3:
                st.json(result)

# --- 📊 SIDEBAR - ANALYTICS & CONTROLS ----------------------------------------
with st.sidebar:
    st.markdown("## 📈 Analytics Dashboard")
    
    # API Health
    health = make_request("GET", "/health")
    
    if health and not health.get("error"):
        st.markdown("### 🟢 System Status")
        st.success(f"**Version:** {health.get('version', '2.0.0')}")
        
        agents = health.get("agents", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Planner", "✅" if agents.get("planner") else "❌")
        col2.metric("Executor", "✅" if agents.get("executor") else "❌")
        col3.metric("Verifier", "✅" if agents.get("verifier") else "❌")
    else:
        st.error("⚠️ API Offline")
    
    st.markdown("---")
    
    # Session Stats
    st.markdown("### 📊 Session Statistics")
    st.metric("Total Queries", st.session_state.total_queries)
    st.metric("Total Cost", f"${st.session_state.total_cost:.6f}")
    
    # Cache Stats
    if health and "cache" in health:
        cache = health["cache"]
        st.markdown("### 💾 Cache Performance")
        
        hits = cache.get("hits", 0)
        misses = cache.get("misses", 0)
        total = hits + misses
        
        if total > 0:
            hit_rate = (hits / total) * 100
            
            fig = go.Figure(data=[go.Pie(
                labels=['Hits', 'Misses'],
                values=[hits, misses],
                hole=0.7,
                marker=dict(colors=['#10b981', '#6366f1']),
                textinfo='none'
            )])
            fig.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=150,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(
                    text=f"{hit_rate:.0f}%",
                    x=0.5, y=0.5,
                    font_size=24,
                    showarrow=False,
                    font_color="white"
                )]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            col1.metric("Hits", hits)
            col2.metric("Misses", misses)
        else:
            st.info("No cache activity yet")
        
        st.markdown(f"**Backend:** {cache.get('backend', 'memory').upper()}")
    
    st.markdown("---")
    
    # Query History
    if st.session_state.history:
        st.markdown("### 📜 Recent Queries")
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            status = "✅" if h['success'] else "⚠️"
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem;">
                {status} <strong>{h['task'][:30]}...</strong><br/>
                <span style="color: #64748b;">⏱️ {h['duration']:.2f}s • 💰 ${h['cost']:.5f}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Actions
    if st.button("🗑️ Clear Cache", use_container_width=True):
        make_request("POST", "/cache/clear")
        st.toast("Cache cleared!", icon="🗑️")
    
    if st.button("🔄 Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.total_cost = 0.0
        st.session_state.total_queries = 0
        st.rerun()
