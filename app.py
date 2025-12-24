import streamlit as st
import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="KitKat AI", page_icon="♥", layout="centered")

# --- FORCE THEME CSS (Crucial Fix) ---
st.markdown("""
<style>
    /* Force the main background color */
    .stApp {
        background-color: #FFF0F5 !important;
    }
    
    /* Force Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #FFE4E8 !important;
    }

    /* Force ALL text to be dark grey (fixes the invisibility issue) */
    .stMarkdown, .stText, h1, h2, h3, p, span, div, label {
        color: #4A4A4A !important;
    }
    
    /* Fix the Chat Input Box */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #333333 !important; /* Dark text inside box */
        border: 2px solid #D84378 !important;
        border-radius: 20px !important;
    }
    
    /* Fix Chat Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Differentiate User vs Bot Bubbles */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #FFE4E1 !important; /* Light pink for user */
    }

    /* Button Styling */
    .stButton button {
        background-color: #FFFFFF !important;
        color: #D84378 !important;
        border: 1px solid #D84378 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #D84378 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BACKEND LOGIC ---
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
    st.markdown("<h1 style='color: #D84378 !important;'>KitKat AI ♥</h1>", unsafe_allow_html=True)
    st.caption("Status: ● Online")
    
    st.write("---")
    
    if st.button("♥  Write to Diary"):
        st.session_state.mode = "write"
        st.success("Mode Active: Type your entry below!")
        
    if st.button("📖  Read Diary"):
        st.session_state.mode = "read"
        st.info("Mode Active: Type the title to search.")

    if st.button("🗑  Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN CHAT ---
# Custom Title (with explicit color to be safe)
st.markdown("<h2 style='text-align: center; color: #D84378;'>How can I help you today?</h2>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message KitKat..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process Input
    response = ""
    mode = getattr(st.session_state, 'mode', None)
    
    # 1. Plugin Mode
    if mode == "write" and 'note' in plugins:
        response = plugins['note'](CONFIG, f"Entry :: {prompt}")
        st.session_state.mode = None # Reset mode
    elif mode == "read" and 'vault_read' in plugins:
        response = plugins['vault_read'](CONFIG, prompt)
        st.session_state.mode = None # Reset mode
    
    # 2. Command Mode (e.g. "system")
    elif prompt.split()[0].lower() in plugins:
        cmd = prompt.split()[0].lower()
        arg = prompt.split(" ", 1)[1] if " " in prompt else ""
        response = plugins[cmd](CONFIG, arg) if arg else plugins[cmd](CONFIG)
        
    # 3. AI Mode
    else:
        try:
            genai.configure(api_key=key)
            # Use the newer model name we found earlier
            model = genai.GenerativeModel('gemini-2.0-flash') 
            res = model.generate_content(prompt)
            response = res.text
        except Exception as e:
            # Fallback for offline/error
            response = "I'm currently offline, my love. (Check terminal for error)"
            print(f"Error: {e}")

    # Assistant Message
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})