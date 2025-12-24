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
    layout="wide", # Use wide mode for a more expansive feel
    initial_sidebar_state="expanded"
)

# --- 2. ENHANCED CSS STYLING ---
st.markdown("""
    <style>
        /* Import a modern, friendly font */
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');

        :root {
            --primary-color: #D81B60; /* Deep Rose */
            --secondary-color: #FFC1CC; /* Light Pink Border */
            --bg-gradient-start: #FFF0F5; /* Lavender Blush */
            --bg-gradient-end: #FFE4E1; /* Misty Rose */
            --text-color: #333333; /* Dark Charcoal for readability */
            --sidebar-bg: rgba(255, 255, 255, 0.85);
            --glass-bg: rgba(255, 255, 255, 0.75);
            --glass-border: 1px solid rgba(255, 255, 255, 0.6);
        }

        /* Base Styles - Force Light Theme & Font */
        html, body, [class*="css"] {
            font-family: 'Quicksand', sans-serif;
            color: var(--text-color) !important;
            background-color: transparent !important; /* Let gradient show */
        }

        /* Main App Background Gradient */
        .stApp {
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
            background-attachment: fixed;
        }

        /* Hide default Streamlit UI elements */
        #MainMenu, footer, header[data-testid="stHeader"] {
            visibility: hidden;
            height: 0;
        }

        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            backdrop-filter: blur(12px); /* Glass effect */
            border-right: var(--glass-border);
            box-shadow: 5px 0 20px rgba(0, 0, 0, 0.05);
        }

        .sidebar-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: -webkit-linear-gradient(45deg, var(--primary-color), #FF80AB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 1.5rem;
            filter: drop-shadow(0px 2px 2px rgba(216, 27, 96, 0.1));
        }

        /* Animated Sidebar Buttons */
        .stButton button {
            background: linear-gradient(to right, #ffffff, #FFF0F5);
            color: var(--primary-color);
            border: 2px solid var(--secondary-color);
            border-radius: 30px;
            padding: 0.7rem 1.2rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Bouncy transition */
            box-shadow: 0 4px 6px rgba(216, 27, 96, 0.1);
            width: 100%;
        }

        .stButton button:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 10px 20px rgba(216, 27, 96, 0.25);
            background: linear-gradient(to right, var(--primary-color), #C2185B);
            color: white;
            border-color: transparent;
        }

        /* --- CHAT AREA ANIMATIONS & STYLING --- */
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Apply animation to new messages */
        .stChatMessage {
            animation: slideInUp 0.5s ease-out both;
        }

        /* Chat Message Bubble Container */
        .stChatMessage > div {
            background-color: var(--glass-bg) !important;
            backdrop-filter: blur(8px);
            border-radius: 22px !important;
            padding: 1.5rem !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.07) !important;
            border: var(--glass-border) !important;
            margin-bottom: 1.2rem;
        }

        /* User Bubble Style */
        div[data-testid="stChatMessage"][data-testid*="user"] > div {
            background: linear-gradient(135deg, #FFF0F5, #FFEAEE) !important;
            border-bottom-right-radius: 4px !important;
        }

        /* Assistant Bubble Style */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div {
            background: linear-gradient(135deg, #FFFFFF, #FAFAFA) !important;
            border-bottom-left-radius: 4px !important;
        }

        /* --- FLOATING CHAT INPUT --- */
        .stChatInput {
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            width: 85%;
            max-width: 900px;
            z-index: 999;
        }
        
        /* Make the container transparent */
        .stChatInput > div { background-color: transparent !important; box-shadow: none !important; }
        /* Hide the bottom block container */
        div[data-testid="stBottom"] { background: transparent; }

        /* Style the input textarea */
        .stChatInput textarea {
            background: var(--glass-bg) !important;
            backdrop-filter: blur(15px);
            border: 2px solid var(--secondary-color) !important;
            border-radius: 35px !important;
            padding: 1.1rem 1.8rem !important;
            color: var(--text-color) !important;
            font-size: 1.05rem;
            box-shadow: 0 10px 35px -5px rgba(216, 27, 96, 0.2) !important;
            transition: all 0.3s ease;
        }

        .stChatInput textarea:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 15px 40px -5px rgba(216, 27, 96, 0.3) !important;
            transform: translateY(-2px);
        }

        /* --- WELCOME SCREEN --- */
        .welcome-container {
            text-align: center;
            padding: 4rem 3rem;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border-radius: 35px;
            border: var(--glass-border);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
            margin: 4rem auto;
            max-width: 750px;
            animation: slideInUp 0.7s ease-out;
        }

        .welcome-icon { font-size: 5rem; margin-bottom: 1rem; animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }

        .welcome-title {
            font-size: 3.5rem;
            font-weight: 900;
            background: -webkit-linear-gradient(45deg, var(--primary-color), #FF80AB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }

        .welcome-text { font-size: 1.3rem; color: #666; line-height: 1.7; }
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

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<div class='sidebar-title'>KitKat AI ♥</div>", unsafe_allow_html=True)
    
    st.write("") # Add some vertical spacing
    
    col1, col2 = st.columns([1, 5])
    with col1: st.write("") # Spacing column
    with col2:
        if st.button("♥  New Diary Entry"):
            st.session_state.mode = "write"
            st.toast("Ready to listen... Type your entry!", icon="🖊️")
            
        if st.button("📖  Read Past Entries"):
            st.session_state.mode = "read"
            st.toast("Search mode: Type a title to retrieve.", icon="🔍")

        if st.button("⚡  System Status"):
             if 'system' in plugins:
                 # Add system info as a bot message
                 st.session_state.messages.append({"role": "assistant", "content": plugins['system'](CONFIG)})
                 st.rerun()

    st.divider()
    
    _, col_clear = st.columns([1, 5])
    with col_clear:
        if st.button("🗑  Clear History"):
            st.session_state.messages = []
            st.rerun()

# --- 7. AI LOGIC WITH ANIMATED STREAMING ---
def stream_ai_response(prompt, key):
    """Generates the AI response and streams it for a typing effect."""
    if not key:
        yield "⚠️ Error: API Key not found. Please check your setup."
        return

    try:
        genai.configure(api_key=key)
        # Use gemini-1.5-flash as the primary reliable model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Stream the response
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text:
                yield char
                # Tiny delay to simulate natural typing speed
                time.sleep(0.015)
                
    except Exception as e:
        yield f"😓 Connection trouble: {e}. Please try again."

# --- 8. MAIN APPLICATION INTERFACE ---

# Display Welcome Screen if chat is empty
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">💖</div>
            <div class="welcome-title">Hi, I'm KitKat!</div>
            <div class="welcome-text">
                Your personal AI companion, wrapped in a beautiful design.<br>
                I'm here to chat, help you write, and keep your secrets safe.
                <br><br>
                <b>✨ Type a message below to begin...</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle New User Input
if prompt := st.chat_input("✨ Message KitKat..."):
    # 1. Add & Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = ""
    mode = getattr(st.session_state, 'mode', None)

    # 2. Handle Plugin Commands (Instant Response)
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
        
        # Display plugin response immediately
        with st.chat_message("assistant"):
            st.markdown(response)
    
    # 3. Handle AI Chat (Animated Streaming Response)
    else:
        with st.chat_message("assistant"):
            # Create a placeholder for the streaming text
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response chunk by chunk
            for chunk in stream_ai_response(prompt, key):
                full_response += chunk
                # Add a blinking cursor effect while typing
                message_placeholder.markdown(full_response + "▌")
            
            # Final update without the cursor
            message_placeholder.markdown(full_response)
            response = full_response

    # 4. Save Assistant Response to History
    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})