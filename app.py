import streamlit as st
import os
import time
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KitKat AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. DATA SETUP ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHATS_DIR = DATA_DIR / "chats"
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json" # NEW: For remembering logins

CHATS_DIR.mkdir(parents=True, exist_ok=True)

if not USERS_FILE.exists():
    with open(USERS_FILE, "w") as f: json.dump({}, f)
    
if not SESSIONS_FILE.exists():
    with open(SESSIONS_FILE, "w") as f: json.dump({}, f)

# --- 3. SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- 4. AUTHENTICATION & SESSION MANAGER ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open(USERS_FILE, "r") as f: return json.load(f)
    except: return {}

def save_user(username, password):
    users = load_users()
    if username in users: return False
    users[username] = hash_password(password)
    with open(USERS_FILE, "w") as f: json.dump(users, f, indent=4)
    return True

def verify_login(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False

# --- NEW: AUTO-LOGIN LOGIC ---
def create_session(username):
    """Creates a token and saves it to keep user logged in."""
    token = str(uuid.uuid4())
    try:
        with open(SESSIONS_FILE, "r") as f: sessions = json.load(f)
    except: sessions = {}
    
    sessions[token] = username
    with open(SESSIONS_FILE, "w") as f: json.dump(sessions, f)
    
    # Set token in URL so browser remembers it on refresh
    st.query_params["token"] = token 
    return token

def check_session():
    """Checks URL for token and auto-logs in."""
    if st.session_state.logged_in: return # Already logged in
    
    params = st.query_params
    token = params.get("token", None)
    
    if token:
        try:
            with open(SESSIONS_FILE, "r") as f: sessions = json.load(f)
            if token in sessions:
                st.session_state.username = sessions[token]
                st.session_state.logged_in = True
                return True
        except: pass
    return False

def logout():
    # Remove session from file
    params = st.query_params
    token = params.get("token", None)
    if token:
        try:
            with open(SESSIONS_FILE, "r") as f: sessions = json.load(f)
            if token in sessions:
                del sessions[token]
                with open(SESSIONS_FILE, "w") as f: json.dump(sessions, f)
        except: pass

    # Clear state
    st.query_params.clear() # Remove token from URL
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.messages = []
    st.rerun()

# --- 5. CHAT STORAGE & DELETION ---
def get_chat_title(messages):
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:40]
            if len(msg["content"]) > 40: title += "..."
            return title
    return "New Conversation"

def save_chat_history():
    if not st.session_state.messages: return
    current_title = get_chat_title(st.session_state.messages)
    file_path = CHATS_DIR / f"{st.session_state.session_id}.json"
    
    chat_data = {
        "id": st.session_state.session_id,
        "username": st.session_state.username,
        "title": current_title,
        "timestamp": datetime.now().isoformat(),
        "messages": st.session_state.messages
    }
    with open(file_path, "w") as f: json.dump(chat_data, f, indent=4)

def load_chat_from_file(filename):
    file_path = CHATS_DIR / filename
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if data.get("username") != st.session_state.username:
                st.error("Access Denied.")
                return
            st.session_state.messages = data["messages"]
            st.session_state.session_id = data["id"]
            st.session_state.page = "home"
            st.rerun()
    except Exception as e: st.error(f"Error: {e}")

def delete_chat_file(filename):
    """Permanently deletes a chat file."""
    file_path = CHATS_DIR / filename
    try:
        if file_path.exists():
            os.remove(file_path)
            st.toast("Chat Deleted Successfully")
            time.sleep(0.5)
            st.rerun()
    except Exception as e: st.error(f"Delete Failed: {e}")

def get_my_history():
    my_chats = []
    files = list(CHATS_DIR.glob("*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    for f in files:
        try:
            with open(f, "r") as file:
                data = json.load(file)
                if data.get("username") == st.session_state.username:
                    my_chats.append({
                        "filename": f.name,
                        "title": data.get("title", "Untitled"),
                        "timestamp": data.get("timestamp", ""),
                        "id": data.get("id", "")
                    })
        except: continue
    return my_chats

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

def start_new_chat():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    navigate_to("home")

# --- 6. AI ENGINE ---
try:
    key = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

def stream_ai_response(prompt):
    if not key: yield "System Error: API Key missing."; return
    genai.configure(api_key=key)
    models = ["gemini-flash-latest", "gemini-pro"]
    active_model = None
    for m in models:
        try:
            test_model = genai.GenerativeModel(m)
            active_model = test_model
            break
        except: continue
    if not active_model: yield "Connection Failed."; return
    try:
        response = active_model.generate_content(prompt, stream=True)
        for chunk in response:
            for char in chunk.text: yield char; time.sleep(0.005)
    except Exception as e: yield f"Error: {str(e)}"

# --- 7. CSS STYLING ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Inter:wght@400;600&display=swap');

        :root {
            --bg-color: #0a0a12;        
            --neon-blue: #00f3ff;
            --neon-purple: #bc13fe;
            --text-main: #ffffff;
            --border-color: rgba(255, 255, 255, 0.1);
            --danger-red: #ff3333;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
        }

        /* BACKGROUND */
        .stApp {
            background: radial-gradient(circle at 20% 20%, rgba(188, 19, 254, 0.15) 0%, transparent 40%),
                        radial-gradient(circle at 80% 80%, rgba(0, 243, 255, 0.15) 0%, transparent 40%),
                        var(--bg-color);
            background-attachment: fixed;
            margin-top: 60px;
        }

        /* LOGIN CONTAINER */
        div[data-testid="column"]:nth-of-type(2) {
            background: rgba(20, 20, 35, 0.9);
            border: 1px solid var(--neon-purple);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 0 40px rgba(188, 19, 254, 0.15);
            text-align: center;
        }

        /* NAVBAR */
        div[data-testid="stVerticalBlock"] > div:first-child > div[data-testid="stHorizontalBlock"] {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 70px;
            background: rgba(10, 10, 18, 0.95);
            backdrop-filter: blur(15px);
            border-bottom: 1px solid var(--border-color);
            z-index: 99999;
            padding: 0 30px;
            align-items: center;
            margin-top: 0 !important;
        }

        /* BUTTONS */
        div.stButton > button {
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #ccc !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            transition: 0.3s;
            padding: 5px 15px !important;
            width: 100%;
        }
        div.stButton > button:hover {
            color: var(--neon-blue) !important;
            border: 1px solid var(--neon-blue) !important;
            background: rgba(0, 243, 255, 0.1) !important;
        }
        
        /* LOGO BUTTON STYLE */
        div[data-testid="column"]:first-child button {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            border: none !important;
            text-align: left !important;
            padding-left: 0 !important;
        }
        div[data-testid="column"]:first-child button:hover {
            box-shadow: none !important;
            border: none !important;
            background: transparent !important;
        }
        
        /* DELETE BUTTON SPECIFIC STYLE */
        /* We can't target just one button easily in pure Streamlit CSS without custom components, 
           but the button text "DEL" will be small enough. */

        /* INPUT BOX */
        .stChatInput { padding-bottom: 100px !important; }
        .stChatInput textarea {
            background-color: rgba(0,0,0,0.5) !important;
            border: 1px solid var(--border-color) !important;
            color: white !important;
            border-radius: 12px !important;
        }
        .stChatInput textarea:focus {
            border-color: var(--neon-blue) !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2) !important;
        }

        /* WATERMARK */
        .watermark {
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            font-size: 15vw; font-weight: 900;
            color: rgba(255,255,255,0.05);
            pointer-events: none; z-index: 0;
            font-family: 'Rajdhani', sans-serif;
            white-space: nowrap;
        }

        section[data-testid="stSidebar"], header[data-testid="stHeader"], div[data-testid="stToolbar"] { display: none !important; }
        
        .content-card {
            background: rgba(20, 20, 35, 0.7);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
    </style>
""", unsafe_allow_html=True)

# --- 8. AUTH PAGE ---
def login_page():
    st.markdown('<div class="watermark">KITKAT AI</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
            <h1 style="font-family:'Rajdhani'; font-size:4rem; background:linear-gradient(to right, #00f3ff, #bc13fe); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">KITKAT AI</h1>
            <p style="color:#888; letter-spacing:2px;">SECURE NEURAL INTERFACE v5.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        choice = st.radio("Access Mode", ["Login", "Register"], horizontal=True)
        st.write("") 
        user = st.text_input("Username")
        pasw = st.text_input("Password", type="password")
        st.write("") 
        if choice == "Login":
            if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
                if verify_login(user, pasw):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    create_session(user) # SAVE SESSION
                    st.rerun()
                else: st.error("Access Denied")
        else:
            if st.button("INITIALIZE ID", use_container_width=True):
                if save_user(user, pasw): st.success("ID Created. Proceed to Login.")
                else: st.error("User exists.")

# --- 9. MAIN APP ---
# CHECK FOR AUTO-LOGIN BEFORE RENDERING
if not st.session_state.logged_in:
    if check_session(): st.rerun() # Auto-login success
    else: login_page()
else:
    # BACKGROUND WATERMARK
    st.markdown('<div class="watermark">KITKAT AI</div>', unsafe_allow_html=True)
    
    # NAVBAR
    with st.container():
        col_logo, col_space, col_h, col_n, col_hist, col_a, col_l = st.columns([2.5, 3, 0.8, 0.8, 0.8, 0.8, 0.8], gap="small")
        with col_logo:
            if st.button("KITKAT AI"): navigate_to("home")
        with col_h: 
            if st.button("🏠 Home"): navigate_to("home")
        with col_n: 
            if st.button("➕ New"): start_new_chat()
        with col_hist: 
            if st.button("📜 Logs"): navigate_to("history")
        with col_a: 
            if st.button("ℹ️ Info"): navigate_to("about")
        with col_l: 
            if st.button("🔒 Exit"): logout()

    # --- PAGES ---
    if st.session_state.page == "home":
        if not st.session_state.messages:
            st.markdown(f"""
                <div style="text-align:center; margin-top:100px;">
                    <h1 style="font-family:'Rajdhani'; font-size:4rem; color:white;">WELCOME, {st.session_state.username.upper()}</h1>
                    <p style="color:#888;">SYSTEM ONLINE // READY FOR INPUT</p>
                </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Enter command..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                ph = st.empty()
                full_res = ""
                ph.markdown("`Thinking...`")
                for chunk in stream_ai_response(prompt):
                    full_res += chunk
                    ph.markdown(full_res + "▌")
                ph.markdown(full_res)
            
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            save_chat_history()

    elif st.session_state.page == "history":
        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        st.title("📜 ENCRYPTED LOGS")
        my_chats = get_my_history()
        
        if not my_chats: st.info("No logs found.")
        else:
            for chat in my_chats:
                # Main Chat Info Column, then Load Button, then Delete Button
                c_info, c_load, c_del = st.columns([4, 0.8, 0.8])
                try: dt = datetime.fromisoformat(chat["timestamp"]).strftime("%d %b, %H:%M") 
                except: dt = "Unknown"
                
                with c_info:
                    st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1);">
                        <strong style="color:#00f3ff">{chat['title']}</strong><br><span style="color:#666; font-size:0.8em">{dt}</span></div>""", unsafe_allow_html=True)
                
                with c_load:
                    st.write(""); st.write("") # Alignment
                    if st.button("LOAD", key=f"load_{chat['id']}"): 
                        load_chat_from_file(chat["filename"])
                
                with c_del:
                    st.write(""); st.write("") # Alignment
                    # Using a red color for Delete would require custom CSS hacking per button ID,
                    # so standard button for now, but functionality is key.
                    if st.button("DEL", key=f"del_{chat['id']}"):
                        delete_chat_file(chat["filename"])

    elif st.session_state.page == "about":
        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        st.title("ℹ️ SYSTEM INFORMATION")
        tab1, tab2, tab3 = st.tabs(["⚡ TECH SPECS", "💡 ORIGIN", "👨‍💻 DEVELOPER"])
        
        with tab1:
            st.markdown("""<div class="content-card">
                <h3>Technical Architecture</h3>
                <p><strong>KitKat AI v5.0</strong> is a high-performance neural interface.</p>
                <ul><li><strong>Core:</strong> Gemini 1.5 Pro/Flash Hybrid</li><li><strong>Security:</strong> SHA-256 Auth & Local Encrypted JSON</li><li><strong>UI:</strong> Custom CSS Injection / Streamlit</li></ul>
            </div>""", unsafe_allow_html=True)
            
        with tab2:
            st.markdown("""<div class="content-card">
                <h3>Project Inspiration</h3>
                <p>Designed to replicate the feel of futuristic OS interfaces seen in cyberpunk media.</p>
            </div>""", unsafe_allow_html=True)
            
        with tab3:
            st.markdown("""<div class="content-card">
                <h3>Developer Profile</h3>
                <h2 style="color:#00f3ff;">Akshay Muley</h2>
                <p><strong>Founder, Madhat Sec</strong></p>
                <p>Building the future of secure AI interactions.</p>
            </div>""", unsafe_allow_html=True)