import streamlit as st
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KitKat AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. NEON GLASS THEME CSS ---
st.markdown("""
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Inter:wght@400;600&display=swap');

        :root {
            --bg-color: #0a0a12;        /* Deep Space Black */
            --glass-bg: rgba(20, 20, 35, 0.7);
            --neon-blue: #00f3ff;
            --neon-purple: #bc13fe;
            --text-main: #ffffff;
            --border-color: rgba(255, 255, 255, 0.1);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
        }

        /* --- BACKGROUND GRADIENT --- */
        .stApp {
            background: radial-gradient(circle at 20% 20%, rgba(188, 19, 254, 0.15) 0%, transparent 40%),
                        radial-gradient(circle at 80% 80%, rgba(0, 243, 255, 0.15) 0%, transparent 40%),
                        var(--bg-color);
            background-attachment: fixed;
        }

        /* --- HIDE DEFAULT STREAMLIT HEADER --- */
        header[data-testid="stHeader"], footer, [data-testid="stToolbar"] { display: none !important; }

        /* --- CUSTOM NAVBAR --- */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 70px;
            background: rgba(10, 10, 18, 0.85);
            backdrop-filter: blur(15px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 40px;
            z-index: 9999;
        }
        .nav-logo {
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }
        .nav-links {
            display: flex;
            gap: 25px;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            color: #ccc;
            font-size: 1.1rem;
        }
        .nav-item:hover { color: var(--neon-blue); cursor: pointer; transition: 0.3s; }

        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: var(--glass-bg) !important;
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--border-color);
            margin-top: 70px; /* Push below navbar */
        }
        
        .sidebar-header {
            font-family: 'Rajdhani', sans-serif;
            color: var(--neon-blue);
            font-size: 1.2rem;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }

        /* --- CHAT BUBBLES --- */
        div[data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-bottom: 20px;
        }

        /* User Bubble (Neon Gradient) */
        div[data-testid="stChatMessage"][data-testid*="user"] > div {
            background: linear-gradient(135deg, #2b0052, #1a0033) !important;
            border: 1px solid var(--neon-purple) !important;
            color: white !important;
            border-radius: 15px;
            border-bottom-right-radius: 2px;
            box-shadow: 0 0 15px rgba(188, 19, 254, 0.3);
        }

        /* AI Bubble (Glass) */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px;
            border-bottom-left-radius: 2px;
        }

        /* --- HERO HEADING (CENTERED) --- */
        .hero-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
            margin-top: 50px;
            text-align: center;
            animation: fadeIn 1.2s ease;
        }
        
        .hero-title {
            font-family: 'Rajdhani', sans-serif;
            font-size: 6rem;
            font-weight: 800;
            line-height: 0.9;
            color: white;
            text-transform: uppercase;
            letter-spacing: -2px;
        }
        
        .hero-gradient {
            background: linear-gradient(to right, var(--neon-blue), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            margin-top: 20px;
            font-size: 1.2rem;
            color: #888;
            background: rgba(0,0,0,0.3);
            padding: 10px 25px;
            border-radius: 50px;
            border: 1px solid var(--border-color);
        }

        /* --- INPUT BOX --- */
        .stChatInput { padding-bottom: 40px; }
        .stChatInput textarea {
            background-color: rgba(0,0,0,0.5) !important;
            border: 1px solid var(--border-color) !important;
            color: white !important;
            border-radius: 12px !important;
        }
        .stChatInput textarea:focus {
            border-color: var(--neon-blue) !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2) !important;
        }

        /* --- BUTTONS --- */
        .stButton button {
            background: transparent !important;
            border: 1px solid var(--neon-blue) !important;
            color: var(--neon-blue) !important;
            border-radius: 8px;
            transition: 0.3s;
        }
        .stButton button:hover {
            background: var(--neon-blue) !important;
            color: black !important;
            box-shadow: 0 0 15px var(--neon-blue);
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

    </style>
""", unsafe_allow_html=True)

# --- 3. CUSTOM NAVBAR INJECTION ---
st.markdown("""
    <div class="navbar">
        <div class="nav-logo">KITKAT AI</div>
        <div class="nav-links">
            <span class="nav-item">HOME</span>
            <span class="nav-item">DOCS</span>
            <span class="nav-item">SETTINGS</span>
            <span class="nav-item" style="color:var(--neon-purple);">LOGIN</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 4. BACKEND SETUP ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PLUGINS_DIR = BASE_DIR / "plugins"
DATA_DIR.mkdir(exist_ok=True)
CONFIG = {"DATA_DIR": DATA_DIR}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 5. KEY LOADING ---
try:
    key = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">/// CONTROL PANEL</div>', unsafe_allow_html=True)
    
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()
        
    st.write("") # Spacer
    
    if st.button("📓 Diary Mode"):
        st.session_state.mode = "write"
        st.toast("System: Diary Protocol Engaged")

    if st.button("📂 Archives"):
        st.session_state.mode = "read"
        st.toast("System: Accessing Database")
        
    st.divider()
    st.caption("System Status: ● ONLINE")

# --- 7. AI ENGINE ---
def stream_ai_response(prompt):
    if not key: yield "System Error: API Key missing."; return
    genai.configure(api_key=key)
    models = ["gemini-flash-latest", "gemini-pro"]
    active_model = None
    for m in models:
        try:
            test_model = genai.GenerativeModel(m)
            active_model = test_model
            break
        except: continue
    if not active_model: yield "Connection Failed: No models available."; return
    try:
        response = active_model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text:
                yield char
                time.sleep(0.005)
    except Exception as e: yield f"Runtime Error: {str(e)}"

# --- 8. UI RENDER ---

# --- HERO SECTION (When Empty) ---
if not st.session_state.messages:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">
                THE NEXT GEN<br>
                <span class="hero-gradient">NEURAL INTERFACE</span>
            </div>
            <div class="hero-subtitle">
                POWERED BY KITKAT AI V5.0
            </div>
        </div>
    """, unsafe_allow_html=True)

# Chat History
# Add spacing so chat doesn't hide behind navbar
st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Enter command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # Plugin logic here (abbreviated for cleanliness, assuming plugins loaded same as before)
    # ... (You can paste your plugin loading logic back here if you use plugins)
    
    # AI Response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        for chunk in stream_ai_response(prompt):
            full_res += chunk
            placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})