import streamlit as st
import os
import time
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KitKat AI",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. "ACTUAL ONE" DARK THEME CSS ---
st.markdown("""
    <style>
        /* IMPORT MODERN FONT */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        :root {
            --bg-color: #050505;        /* Deep Black */
            --sidebar-bg: #0A0A0A;      /* Slightly lighter black */
            --card-bg: #141414;         /* Dark Grey Cards */
            --accent: #FF0055;          /* Neon Pink */
            --text-main: #FFFFFF;       /* Pure White */
            --text-sub: #888888;        /* Grey text */
            --border: 1px solid #333;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
        }

        /* --- BACKGROUND --- */
        .stApp {
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 50% 0%, #1a050a 0%, #050505 60%);
        }

        /* --- HIDE JUNK --- */
        header, footer, [data-testid="stToolbar"] { display: none !important; }

        /* --- SIDEBAR --- */
        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid #222;
        }
        
        /* --- CHAT BUBBLES (MINIMALIST) --- */
        div[data-testid="stChatMessage"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-bottom: 20px;
        }

        /* User Message (Right Aligned, Neon Glow) */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background-color: var(--card-bg) !important;
            border: 1px solid #333 !important;
            border-radius: 12px;
            padding: 15px !important;
            border-left: 3px solid var(--accent) !important;
        }

        /* Assistant Message (Clean) */
        div[data-testid="stChatMessage"][data-testid*="assistant"] {
            padding-left: 15px !important;
        }

        /* FORCE TEXT COLORS */
        p, span, div { color: #FFFFFF !important; }
        code { background-color: #222 !important; color: #FF0055 !important; }

        /* --- INPUT BOX (The "Terminal" Look) --- */
        .stChatInput { padding-bottom: 30px; }
        
        .stChatInput textarea {
            background-color: #0A0A0A !important;
            color: #FFFFFF !important;
            border: 1px solid #333 !important;
            border-radius: 12px !important;
        }
        .stChatInput textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.2) !important;
        }

        /* --- BUTTONS --- */
        div.stButton > button {
            background-color: #111 !important;
            color: #FFF !important;
            border: 1px solid #333 !important;
            border-radius: 8px;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
            background-color: #1a1a1a !important;
        }

        /* --- WELCOME HERO --- */
        .hero-container {
            text-align: center;
            margin-top: 100px;
            animation: fadeIn 1s ease;
        }
        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: -2px;
            background: linear-gradient(to right, #FFF, #888);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #666 !important;
            margin-top: 10px;
        }
        .accent-text { color: var(--accent) !important; display: inline; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PLUGINS_DIR = BASE_DIR / "plugins"
DATA_DIR.mkdir(exist_ok=True)
CONFIG = {"DATA_DIR": DATA_DIR}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. KEY LOADING ---
try:
    key = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

# --- 5. PLUGINS ---
def load_plugins():
    plugins = {}
    if PLUGINS_DIR.exists():
        for f in PLUGINS_DIR.glob("*.py"):
            if f.name == "__init__.py": continue
            try:
                spec = importlib.util.spec_from_file_location(f.stem, f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'register'):
                    plugins.update(mod.register(CONFIG))
            except: pass
    return plugins

plugins = load_plugins()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:white; border-bottom:1px solid #333; padding-bottom:10px;'>/// MENU</h3>", unsafe_allow_html=True)
    st.write("")
    if st.button("New Entry"):
        st.session_state.mode = "write"
        st.toast("System: Ready for input", icon="⚫")
    if st.button("Access Archives"):
        st.session_state.mode = "read"
        st.toast("System: Searching database", icon="⚫")
    if st.button("Purge Logs"):
        st.session_state.messages = []
        st.rerun()

# --- 7. AI ENGINE (STREAMING) ---
def stream_ai_response(prompt):
    if not key:
        yield "System Error: API Key missing."
        return

    genai.configure(api_key=key)
    models = ["gemini-flash-latest", "gemini-pro"] # Connection fallback
    
    active_model = None
    for m in models:
        try:
            test_model = genai.GenerativeModel(m)
            active_model = test_model
            break
        except: continue
    
    if not active_model:
        yield "Connection Failed: No models available."
        return

    try:
        response = active_model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text:
                yield char
                time.sleep(0.005)
    except Exception as e:
        yield f"Runtime Error: {str(e)}"

# --- 8. UI RENDER ---

# Hero Screen (If empty)
if not st.session_state.messages:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">KitKat <span class="accent-text">AI</span></div>
            <div class="hero-subtitle">Personal Neural Interface v5.0</div>
            <br><br>
            <p style="color:#444 !important; font-size: 0.9rem;">ENCRYPTED // SECURE // ONLINE</p>
        </div>
    """, unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Enter command or message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    if mode == "write" and 'note' in plugins:
        response = plugins['note'](CONFIG, f"Entry :: {prompt}")
        st.session_state.mode = None
    elif mode == "read" and 'vault_read' in plugins:
        response = plugins['vault_read'](CONFIG, prompt)
        st.session_state.mode = None
    elif prompt.split()[0].lower() in plugins:
        cmd = prompt.split()[0].lower()
        arg = prompt.split(" ", 1)[1] if " " in prompt else ""
        response = plugins[cmd](CONFIG, arg) if arg else plugins[cmd](CONFIG)
        with st.chat_message("assistant"):
            st.markdown(response)
    else:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            for chunk in stream_ai_response(prompt):
                full_res += chunk
                placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            response = full_res

    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})