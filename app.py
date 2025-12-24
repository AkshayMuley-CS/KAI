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
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. NEW BACKGROUND DESIGN ---
st.markdown("""
    <style>
        /* IMPORT FONT */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

        /* --- GLOBAL VARIABLES --- */
        :root {
            --primary: #FF4081;         /* Bright Pink */
            --text-dark: #2C3E50;       /* Dark Grey */
        }

        /* FORCE FONT */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            color: var(--text-dark) !important;
        }

        /* --- THE NEW BACKGROUND (Gradient) --- */
        .stApp {
            /* Soft Rose to Peach Gradient */
            background: linear-gradient(135deg, #FFF5F7 0%, #FFE4E1 100%);
            background-attachment: fixed;
        }

        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        header[data-testid="stHeader"], footer, [data-testid="stToolbar"] {
            display: none !important;
        }

        /* --- SIDEBAR (Glass Effect) --- */
        section[data-testid="stSidebar"] {
            background-color: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(10px); /* Frosted Glass */
            border-right: 1px solid rgba(255,255,255,0.5);
        }
        
        .title-text {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(to right, #FF4081, #FF80AB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 20px;
        }

        /* --- CHAT BUBBLES --- */
        div[data-testid="stChatMessage"] {
            border-radius: 20px !important;
            padding: 1.5rem !important;
            border: 1px solid rgba(255,255,255,0.5) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        }

        /* USER BUBBLE (Pink Gradient) */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            background: linear-gradient(135deg, #FF80AB, #FF4081) !important;
        }
        /* User Text White */
        div[data-testid="stChatMessage"][data-testid*="user"] p,
        div[data-testid="stChatMessage"][data-testid*="user"] div {
            color: white !important;
        }

        /* ASSISTANT BUBBLE (White Glass) */
        div[data-testid="stChatMessage"][data-testid*="assistant"] {
            background-color: rgba(255, 255, 255, 0.85) !important;
        }

        /* --- INPUT BOX (Floating) --- */
        .stChatInput {
            padding-bottom: 30px;
        }
        .stChatInput textarea {
            background-color: white !important;
            color: #333 !important;
            border: 2px solid #FFC1CC !important; /* Soft Pink Border */
            border-radius: 50px !important;
            padding: 15px 25px !important;
            box-shadow: 0 5px 20px rgba(255, 193, 204, 0.4) !important;
        }
        .stChatInput textarea:focus {
            border-color: #FF4081 !important;
            box-shadow: 0 5px 25px rgba(255, 64, 129, 0.3) !important;
        }

        /* --- BUTTONS --- */
        .stButton button {
            background-color: white !important;
            color: #FF4081 !important;
            border: 1px solid #FF4081 !important;
            border-radius: 15px !important;
            font-weight: 600 !important;
        }
        .stButton button:hover {
            background-color: #FF4081 !important;
            color: white !important;
            transform: translateY(-2px);
        }

        /* WELCOME CARD */
        .welcome-box {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 50px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(255, 64, 129, 0.1);
            border: 1px solid white;
            margin-top: 60px;
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

# --- 7. AI ENGINE ---
def stream_ai_response(prompt):
    if not key:
        yield "⚠️ API Key missing."
        return

    genai.configure(api_key=key)
    
    # Using 'gemini-flash-latest' to ensure connection works
    models_to_try = ["gemini-flash-latest", "gemini-pro"]
    
    active_model = None
    for m in models_to_try:
        try:
            test_model = genai.GenerativeModel(m)
            active_model = test_model
            break
        except: continue
    
    if not active_model:
        yield "⚠️ Connection Error. Please refresh."
        return

    try:
        response = active_model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text:
                yield char
                time.sleep(0.005)
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"

# --- 8. MAIN UI ---

# Welcome Screen
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-box">
            <h1 style="color: #FF4081; font-size: 3.5rem;">🌸 Hello!</h1>
            <p style="font-size: 1.3rem; color: #555;">
                I'm <b>KitKat</b>.
                <br>Your world, my words.
            </p>
        </div>
    """, unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Handling
if prompt := st.chat_input("Type something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # Logic
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