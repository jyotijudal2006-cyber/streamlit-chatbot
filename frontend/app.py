import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/v1"

# Set page config
st.set_page_config(
    page_title="Modern AI Chatbot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design
st.markdown("""
<style>
    /* Global modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Vibrant modern theme header */
    h1 {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    /* Subheader and sidebar titles */
    h2, h3 {
        color: #2D3748 !important;
        font-weight: 600 !important;
    }
    
    /* Custom button styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(50,50,93,0.11), 0 1px 3px rgba(0,0,0,0.08);
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 14px rgba(50,50,93,0.1), 0 3px 6px rgba(0,0,0,0.08);
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []


def fetch_history():
    """Fetch chat history from the backend."""
    if st.session_state.session_id:
        try:
            response = requests.get(f"{API_URL}/history/{st.session_state.session_id}")
            if response.status_code == 200:
                st.session_state.messages = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")

# Sidebar for file upload
with st.sidebar:
    st.title("✨ Modern AI Chatbot")
    st.markdown("Upload documents (PDF, DOCX, TXT) and ask questions about them.")
    st.divider()

    st.header("Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="document_uploader"
    )

    if st.button("Process Documents", key="process_documents"):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                all_success = True
                for file in uploaded_files:
                    if file.name in st.session_state.uploaded_files:
                        continue

                    files_payload = {
                        "file": (file.name, file.getvalue(), file.type)
                    }
                    data_payload = {}
                    if st.session_state.session_id:
                        data_payload["session_id"] = st.session_state.session_id

                    try:
                        response = requests.post(f"{API_URL}/upload", files=files_payload, data=data_payload, timeout=120)
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.session_id = result.get("session_id")
                            st.session_state.uploaded_files.append(file.name)
                            st.success(f"✅ {file.name} processed successfully!")
                        else:
                            all_success = False
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"❌ Failed to process {file.name}: {error_detail}")
                    except requests.exceptions.RequestException as e:
                        all_success = False
                        st.error(f"❌ Error connecting to backend: {e}")

                if all_success:
                    st.success("All documents processed and ready for questions!")
        else:
            st.warning("Please select at least one file to upload.")

    st.divider()
    if st.session_state.uploaded_files:
        st.subheader("Uploaded Documents in Session:")
        for f in st.session_state.uploaded_files:
            st.text(f"• {f}")

# Main chat interface
st.title("Modern AI Chatbot")

if not st.session_state.uploaded_files:
    st.info("👋 Welcome! Please upload a document in the sidebar to start chatting.")

# Sync history from backend initially if needed
if st.session_state.session_id and not st.session_state.messages:
    fetch_history()

# Display chat history from state
for msg in st.session_state.messages:
    role = msg.get("role") if isinstance(msg, dict) else msg.role
    content = msg.get("content") if isinstance(msg, dict) else msg.content
    with st.chat_message(role):
        st.markdown(content)

if prompt := st.chat_input("Ask a question about your documents..."):
    if not st.session_state.session_id or not st.session_state.uploaded_files:
        st.warning("Please upload a document first.")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt
                }
                try:
                    response = requests.post(f"{API_URL}/chat", json=payload, timeout=60)
                    if response.status_code == 200:
                        answer = response.json().get("answer")
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_detail = response.json().get("detail", "Error generating response.")
                        st.error(f"Error: {error_detail}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_detail}"})
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to backend: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": "Connection error."})
