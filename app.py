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
    page_icon="♥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "GLASS ROSE" DESIGN SYSTEM (CSS) ---
st.markdown("""
    <style>
        /* --- GLOBAL RESET & FONTS --- */
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap');
        
        :root {
            --bg-color: #FFF0F5;
            --accent-color: #D81B60;
            --text-color: #424242;
            --glass-white: rgba(255, 255, 255, 0.95);
        }

        html, body, [class*="css"] {
            font-family: 'Quicksand', sans-serif;
            color: var(--text-color);
        }

        /* --- BACKGROUND GRADIENT --- */
        .stApp {
            background: linear-gradient(135deg, #FFF0F5 0%, #FFD1DC 100%);
            background-attachment: fixed;
        }

        /* --- FIXING THE "BLACK BAR" AT THE BOTTOM --- */
        .stBottom, div[data-testid="stBottom"] {
            background-color: transparent !important;
            border: none !important;
        }
        div[data-testid="stBottom"] > div {
            background-color: transparent !important;
        }

        /* --- INPUT BOX STYLING (FLOATING PILL) --- */
        .stChatInput {
            padding-bottom: 20px;
        }
        .stChatInput textarea {
            background-color: white !important;
            color: #333 !important;
            border-radius: 30px !important;
            border: 2px solid #FFC1CC !important;
            box-shadow: 0 4px 15px rgba(216, 27, 96, 0.1) !important;
        }
        .stChatInput textarea:focus {
            border-color: #D81B60 !important;
            box-shadow: 0 4px 20px rgba(216, 27, 96, 0.2) !important;
        }

        /* --- CHAT BUBBLES --- */
        div[data-testid="stChatMessage"] {
            background-color: var(--glass-white);
            border-radius: 20px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.5);
        }
        
        /* User Bubble */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background-color: #FFEAEE;
            border-bottom-right-radius: 5px;
        }
        
        /* Bot Bubble */
        div[data-testid="stChatMessage"][data-testid*="assistant"] {
            background-color: #FFFFFF;
            border-bottom-left-radius: 5px;
        }

        /* --- HIDE UGLY ELEMENTS --- */
        header[data-testid="stHeader"] { visibility: hidden; }
        [data-testid="stToolbar"] { visibility: hidden; }
        footer { visibility: hidden; }
        .stDeployButton { display: none; }
        
        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #FFE4E1;
        }
        
        /* --- CUSTOM BUTTONS --- */
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            border: 1px solid #FFC1CC;
            color: #D81B60;
            background-color: white;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        div.stButton > button:hover {
            background-color: #D81B60;
            color: white;
            border-color: #D81B60;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(216, 27, 96, 0.2);
        }
        
        /* --- WELCOME CARD --- */
        .welcome-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-top: 50px;
            box-shadow: 0 10px 30px rgba(216, 27, 96, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        .welcome-title {
            font-size: 2.5rem;
            color: #D81B60;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .welcome-subtitle {
            font-size: 1.1rem;
            color: #666;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND SETUP ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PLUGINS_DIR = BASE_DIR / "plugins"
DATA_DIR.mkdir(exist_ok=True)
CONFIG = {"DATA_DIR": DATA_DIR}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. LOAD CREDENTIALS ---
try:
    key = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

# --- 5. LOAD PLUGINS ---
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
    st.markdown("<h2 style='text-align: center; color: #D81B60;'>Menu</h2>", unsafe_allow_html=True)
    
    st.write("") # Spacing
    
    if st.button("♥  Write to Diary"):
        st.session_state.mode = "write"
        st.toast("Diary Mode Active: Type your entry!", icon="♥")
        
    if st.button("📖  Read Diary"):
        st.session_state.mode = "read"
        st.toast("Reading Mode: Type a title to search.", icon="📖")

    if st.button("⚡  System Health"):
        if 'system' in plugins:
            st.session_state.messages.append({"role": "assistant", "content": plugins['system'](CONFIG)})
            st.rerun()

    st.divider()
    
    if st.button("🗑  Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 7. AI ENGINE ---
def get_ai_response(prompt):
    if not key: return "Error: No API Key found."
    genai.configure(api_key=key)
    
    # Priority list to avoid 404/429
    models = ["gemini-1.5-flash", "gemini-flash-latest", "gemini-pro"]
    
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(prompt).text
        except: continue
            
    return "I'm having trouble connecting. Please try again in a moment. ♥"

# --- 8. MAIN UI LOGIC ---

# A. If Chat is Empty -> Show "Welcome Card" to fill space
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-card">
            <div class="welcome-title">KitKat AI</div>
            <div class="welcome-subtitle">Your personal companion, always here for you.</div>
            <br>
            <p style='color: #888; font-size: 0.9rem;'>
                Try asking: "How are you?" or click "Write to Diary"
            </p>
        </div>
    """, unsafe_allow_html=True)

# B. Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# C. Handle Input
if prompt := st.chat_input("Message KitKat..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # Plugin Handlers
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
    
    # AI Handler
    else:
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)

    # Add Bot Message
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})