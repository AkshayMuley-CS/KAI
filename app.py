import streamlit as st
import os
import time
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="KitKat AI",
    page_icon="♥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS STYLING (Force Black Text) ---
st.markdown("""
    <style>
        /* IMPORT FONT */
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
        
        /* FORCE ALL TEXT TO BE BLACK */
        * {
            font-family: 'Quicksand', sans-serif !important;
            color: #333333 !important;
        }

        /* APP BACKGROUND */
        .stApp {
            background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%);
        }

        /* HIDE DEFAULT ELEMENTS */
        header, footer, [data-testid="stToolbar"], .stDeployButton {
            display: none !important;
        }

        /* --- CHAT BUBBLES --- */
        div[data-testid="stChatMessage"] {
            background-color: rgba(255, 255, 255, 0.95) !important;
            border-radius: 20px !important;
            border: 1px solid #FFC1CC !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
            padding: 15px !important;
        }
        
        /* User Bubble Color */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background-color: #FFEAEE !important;
        }

        /* CRITICAL: FORCE CHAT TEXT VISIBILITY */
        div[data-testid="stChatMessage"] p, 
        div[data-testid="stChatMessage"] div {
            color: #000000 !important;
            font-weight: 500 !important;
        }

        /* --- INPUT BOX --- */
        .stChatInput textarea {
            background-color: #FFFFFF !important;
            color: #000000 !important; /* Force Black Text */
            caret-color: #D81B60 !important; /* Pink Cursor */
            border: 2px solid #FFC1CC !important;
            border-radius: 30px !important;
        }
        
        /* HIDE BLACK BOTTOM BAR */
        .stBottom { background-color: transparent !important; }
        div[data-testid="stBottom"] { background-color: transparent !important; }

        /* --- SIDEBAR BUTTONS --- */
        div.stButton > button {
            background-color: white !important;
            color: #D81B60 !important;
            border: 1px solid #FFC1CC !important;
            border-radius: 12px !important;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #D81B60 !important;
            color: white !important;
            border-color: #D81B60 !important;
        }

        /* WELCOME CARD TEXT */
        .welcome-title { color: #D81B60 !important; font-size: 2.5rem; font-weight: 700; }
        .welcome-subtitle { color: #555 !important; }

    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PLUGINS_DIR = BASE_DIR / "plugins"
DATA_DIR.mkdir(exist_ok=True)
CONFIG = {"DATA_DIR": DATA_DIR}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. LOAD KEY ---
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
    st.markdown("<h2 style='text-align: center; color: #D81B60;'>KitKat Menu</h2>", unsafe_allow_html=True)
    st.write("")
    if st.button("♥ Write to Diary"):
        st.session_state.mode = "write"
        st.toast("Mode: Writing Entry", icon="♥")
    if st.button("📖 Read Diary"):
        st.session_state.mode = "read"
        st.toast("Mode: Reading", icon="📖")
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 7. AI ENGINE ---
def get_ai_response(prompt):
    if not key: return "Error: No API Key found."
    genai.configure(api_key=key)
    models = ["gemini-1.5-flash", "gemini-flash-latest"]
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(prompt).text
        except: continue
    return "I need a moment (Connection Error). Please try again. ♥"

# --- 8. UI RENDER ---
if not st.session_state.messages:
    st.markdown("""
        <div style="text-align: center; padding: 50px; background: rgba(255,255,255,0.7); border-radius: 20px; margin-top: 50px;">
            <div class="welcome-title">KitKat AI</div>
            <div class="welcome-subtitle">Your personal companion, always here for you.</div>
        </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message KitKat..."):
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
    else:
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})