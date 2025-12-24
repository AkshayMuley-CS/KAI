import streamlit as st
import os
import time
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="KitKat AI", page_icon="♥", layout="centered")

# --- CUSTOM CSS (Refined for Rose Gold) ---
st.markdown("""
<style>
    /* Force Input Box Styling */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 2px solid #D84378 !important;
        border-radius: 20px !important;
    }
    /* Chat Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #FFE4E1; /* Pink for user */
    }
    /* Buttons */
    .stButton button {
        color: #D84378 !important;
        border: 1px solid #D84378 !important;
        background-color: white !important;
        border-radius: 10px !important;
    }
    .stButton button:hover {
        background-color: #D84378 !important;
        color: white !important;
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

# --- PLUGINS LOADER ---
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
    st.markdown("<h1 style='color: #D84378;'>KitKat AI ♥</h1>", unsafe_allow_html=True)
    st.caption("Status: ● Online")
    
    st.write("---")
    
    if st.button("♥  Write to Diary"):
        st.session_state.mode = "write"
        st.success("Mode Active: Type your entry!")
        
    if st.button("📖  Read Diary"):
        st.session_state.mode = "read"
        st.info("Mode Active: Type the title.")

    if st.button("🗑  Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- ROBUST AI CONNECTION ---
def get_ai_response(prompt):
    if not key: return "Error: API Key missing."
    
    genai.configure(api_key=key)
    
    # EXACT MODELS FOUND IN YOUR DIAGNOSTIC SCAN
    # We try them in order of speed/reliability
    models = [
        "gemini-1.5-flash",       # Standard Flash
        "gemini-flash-latest",    # Latest Flash alias
        "gemini-2.0-flash-exp",   # New 2.0 (Fast)
        "gemini-pro-latest"       # Stable Pro
    ]
    
    last_err = ""
    
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            # Send message
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_err = str(e)
            if "429" in last_err: # Rate limit
                time.sleep(1) # Wait a tiny bit and try next model
                continue
            elif "404" in last_err: # Model not found
                continue
            else:
                # Actual error (like internet down)
                return f"Connection Error: {e}"

    return "I'm thinking too fast (Rate Limit). Please wait 10 seconds and try again! ♥"

# --- MAIN CHAT UI ---
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

    # 1. Plugin Check
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
    
    # 2. AI Check
    else:
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})