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
    page_icon="🍭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. "CANDY POP" THEME (High Contrast & Bright) ---
st.markdown("""
    <style>
        /* IMPORT FONT */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

        /* --- GLOBAL VARIABLES --- */
        :root {
            --bg-color: #FFFFFF;        /* Pure White */
            --sidebar-bg: #F0F2F6;      /* Light Grey */
            --primary: #FF4081;         /* Bright Pink */
            --secondary: #40C4FF;       /* Bright Blue */
            --text-dark: #2C3E50;       /* Dark Blue-Grey (Readable) */
            --text-light: #FFFFFF;
        }

        /* FORCE LIGHT MODE & FONT */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color) !important;
            color: var(--text-dark) !important;
        }

        /* HIDE DEFAULT STREAMLIT HEADER/FOOTER */
        header[data-testid="stHeader"], footer, [data-testid="stToolbar"] {
            display: none !important;
        }

        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-bg) !important;
            border-right: 2px solid white;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        }
        
        /* TITLE STYLE */
        .title-text {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(to right, #FF4081, #7C4DFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 20px;
        }

        /* --- CHAT BUBBLES (ANIMATED) --- */
        @keyframes popIn {
            0% { opacity: 0; transform: scale(0.9) translateY(10px); }
            100% { opacity: 1; transform: scale(1) translateY(0); }
        }

        .stChatMessage {
            animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        div[data-testid="stChatMessage"] {
            border-radius: 20px !important;
            padding: 1.5rem !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        }

        /* USER BUBBLE (Bright Pink) */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background: linear-gradient(135deg, #FF80AB, #FF4081) !important;
        }
        /* User Text must be WHITE */
        div[data-testid="stChatMessage"][data-testid*="user"] p,
        div[data-testid="stChatMessage"][data-testid*="user"] div {
            color: white !important;
            font-weight: 500;
        }

        /* ASSISTANT BUBBLE (Light Blue/Grey) */
        div[data-testid="stChatMessage"][data-testid*="assistant"] {
            background-color: #F8F9FA !important;
            border: 2px solid #E3E6EA !important;
        }
        /* Assistant Text must be DARK */
        div[data-testid="stChatMessage"][data-testid*="assistant"] p,
        div[data-testid="stChatMessage"][data-testid*="assistant"] div {
            color: #2C3E50 !important;
        }

        /* --- INPUT BOX (Floating Capsule) --- */
        .stChatInput {
            padding-bottom: 30px;
        }
        .stChatInput textarea {
            background-color: white !important;
            color: #333 !important;
            border: 3px solid #FF4081 !important;
            border-radius: 50px !important;
            padding: 15px 25px !important;
            box-shadow: 0 5px 20px rgba(255, 64, 129, 0.2) !important;
        }
        .stChatInput textarea:focus {
            box-shadow: 0 8px 25px rgba(255, 64, 129, 0.4) !important;
        }

        /* --- BUTTONS --- */
        .stButton button {
            background-color: white !important;
            color: #FF4081 !important;
            border: 2px solid #FF4081 !important;
            border-radius: 15px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #FF4081 !important;
            color: white !important;
            transform: translateY(-2px);
        }

        /* WELCOME CARD */
        .welcome-box {
            background: white;
            border-radius: 30px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            border: 1px solid #eee;
            margin-top: 50px;
            animation: popIn 0.6s ease;
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
    st.markdown("<div class='title-text'>KitKat</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>v5.0 Bright Edition</p>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns([1,4])
    with col2:
        if st.button("🖊️  Write Diary"):
            st.session_state.mode = "write"
            st.toast("Mode: Writing Entry", icon="🖊️")
        
        if st.button("🔍  Read Diary"):
            st.session_state.mode = "read"
            st.toast("Mode: Reading", icon="🔍")

        if st.button("🧼  Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# --- 7. AI ENGINE (FIXED MODEL ERROR) ---
def stream_ai_response(prompt):
    if not key:
        yield "⚠️ API Key missing."
        return

    genai.configure(api_key=key)
    
    # FIX: Using 'gemini-flash-latest' which is supported by your account
    # Added fallback to 'gemini-pro' just in case
    models_to_try = ["gemini-flash-latest", "gemini-pro"]
    
    active_model = None
    for m in models_to_try:
        try:
            test_model = genai.GenerativeModel(m)
            # Simple test to see if model is valid before streaming
            active_model = test_model
            break
        except: continue
    
    if not active_model:
        yield "⚠️ Connection Error: No available models found."
        return

    try:
        response = active_model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text:
                yield char
                time.sleep(0.005) # Typing speed
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"

# --- 8. MAIN UI ---

# Welcome Screen
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-box">
            <h1 style="color: #FF4081; font-size: 3rem;">Hello! 👋</h1>
            <p style="font-size: 1.2rem; color: #555;">
                I'm <b>KitKat</b>, your personal AI companion.
                <br>I'm ready to chat, help, or listen.
            </p>
        </div>
    """, unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Handling
if prompt := st.chat_input("Type something fun..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # 2. Plugin Logic
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
    
    # 3. AI Logic (Streaming)
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