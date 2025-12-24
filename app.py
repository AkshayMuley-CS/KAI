import streamlit as st
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KitKat AI",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ELECTRIC BLUE THEME CSS ---
st.markdown("""
    <style>
        /* IMPORT MODERN FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');

        :root {
            --bg-color: #020617;        /* Very Dark Blue */
            --card-bg: #0F172A;         /* Dark Blue-Grey */
            --primary: #00F0FF;         /* Electric Cyan */
            --secondary: #4361EE;       /* Royal Blue */
            --text-main: #F8FAFC;       /* White-ish */
            --glow: rgba(0, 240, 255, 0.5);
        }

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
        }

        /* --- BACKGROUND --- */
        .stApp {
            background: radial-gradient(circle at top center, #1e1b4b 0%, #020617 60%);
            background-attachment: fixed;
        }

        /* --- HIDE DEFAULT UI --- */
        header, footer, [data-testid="stToolbar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none; }

        /* --- HERO SECTION (THE BIG TITLE) --- */
        .hero-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 70vh;
            text-align: center;
            animation: slideUp 1s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .hero-title {
            font-size: 7rem; /* MASSIVE SIZE */
            font-weight: 900;
            letter-spacing: -4px;
            line-height: 1;
            background: linear-gradient(135deg, #FFFFFF 0%, #4361EE 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 50px rgba(67, 97, 238, 0.3);
            margin-bottom: 20px;
        }

        .hero-badge {
            background: rgba(0, 240, 255, 0.1);
            border: 1px solid var(--primary);
            color: var(--primary);
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: 700;
            letter-spacing: 1px;
            box-shadow: 0 0 20px var(--glow);
        }

        @keyframes slideUp { from { opacity: 0; transform: translateY(50px); } to { opacity: 1; transform: translateY(0); } }

        /* --- CHAT BUBBLES --- */
        div[data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-bottom: 20px;
        }

        /* User Message (Right, Blue Gradient) */
        div[data-testid="stChatMessage"][data-testid*="user"] {
            justify-content: flex-end;
        }
        div[data-testid="stChatMessage"][data-testid*="user"] > div {
            background: linear-gradient(135deg, var(--secondary), #3A0CA3) !important;
            color: white !important;
            border-radius: 18px;
            border-bottom-right-radius: 4px;
            padding: 15px 25px !important;
            box-shadow: 0 10px 30px rgba(67, 97, 238, 0.3);
        }

        /* AI Message (Left, Glass Dark) */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid #1E293B !important;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            padding: 15px 25px !important;
        }

        /* --- INPUT BOX (Floating Glow) --- */
        .stChatInput { padding-bottom: 40px; }
        
        .stChatInput textarea {
            background-color: #0F172A !important;
            color: white !important;
            border: 2px solid #1E293B !important;
            border-radius: 15px !important;
            box-shadow: 0 0 0 transparent;
            transition: all 0.3s ease;
        }
        .stChatInput textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 30px var(--glow) !important;
            transform: translateY(-2px);
        }

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

# --- 5. AI ENGINE ---
def stream_ai_response(prompt):
    if not key: yield "System Error: API Key missing."; return
    genai.configure(api_key=key)
    models = ["gemini-1.5-flash", "gemini-pro"]
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

# --- 6. UI RENDER ---

# --- HERO SECTION (VISIBLE WHEN EMPTY) ---
if not st.session_state.messages:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">KITKAT AI</div>
            <div class="hero-badge">⚡ ONLINE & READY</div>
            <p style="color: #64748B; margin-top: 20px;">Ask me anything, or just say hello.</p>
        </div>
    """, unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        for chunk in stream_ai_response(prompt):
            full_res += chunk
            placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})