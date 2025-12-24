import streamlit as st
import os
import time
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="KitKat AI", page_icon="♥", layout="centered", initial_sidebar_state="expanded")

# --- STEALTH MODE & THEME CSS ---
st.markdown("""
    <style>
        /* 1. HIDE STREAMLIT HEADER, DEPLOY BUTTON, & MENU */
        header[data-testid="stHeader"] {
            visibility: hidden;
            height: 0%;
        }
        [data-testid="stToolbar"] {
            visibility: hidden;
            height: 0%;
        }
        div.stDecoration {
            visibility: hidden;
            height: 0%;
        }

        /* 2. FORCE ROSE GOLD THEME */
        :root {
            --primary-color: #D84378;
            --background-color: #FFF0F5;
            --secondary-background-color: #FFE4E8;
            --text-color: #4A4A4A;
            --font: sans-serif;
        }
        .stApp { background-color: #FFF0F5 !important; }
        section[data-testid="stSidebar"] { background-color: #FFE4E8 !important; }
        h1, h2, h3, p, span, div, label, .stMarkdown, .stText { color: #4A4A4A !important; }
        
        /* 3. INPUT BOX STYLING */
        .stChatInput textarea {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border: 2px solid #D84378 !important;
        }
        
        /* 4. CHAT BUBBLES */
        div[data-testid="stChatMessage"] {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border-radius: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background-color: #FFE4E1 !important;
        }
        
        /* 5. BUTTONS */
        div.stButton > button {
            color: #D84378 !important;
            background-color: white !important;
            border: 1px solid #D84378 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND SETUP ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PLUGINS_DIR = BASE_DIR / "plugins"
DATA_DIR.mkdir(exist_ok=True)
CONFIG = {"DATA_DIR": DATA_DIR}

if "messages" not in st.session_state: st.session_state.messages = []

# --- LOAD KEY ---
try:
    key = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

# --- PLUGINS ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #D84378; text-align: center;'>KitKat AI ♥</h1>", unsafe_allow_html=True)
    st.caption("Status: ● Online")
    st.write("---")
    
    if st.button("♥  Write to Diary"):
        st.session_state.mode = "write"
        st.success("Mode: Writing...")
        
    if st.button("📖  Read Diary"):
        st.session_state.mode = "read"
        st.info("Mode: Reading...")

    if st.button("🗑  Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- AI LOGIC ---
def get_ai_response(prompt):
    if not key: return "Error: No API Key found."
    
    try:
        genai.configure(api_key=key)
        # Using gemini-flash-latest to avoid 404 errors
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            return "I need a moment to think (Rate Limit). Please wait 10 seconds. ♥"
        return f"Connection Error: {err_msg}"

# --- MAIN CHAT ---
# Extra spacing to account for hidden header
st.markdown("<div style='margin-top: -50px;'></div>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #D84378;'>How can I help you?</h3>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message KitKat..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # Plugins
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
    
    # AI
    else:
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})