import os
import re
import sys
import uuid

# --- Path Configuration ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import streamlit.components.v1 as components
from src.agent.config import llm
from src.agent.main import run_agent

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Your Tech Guy", layout="wide")

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_model" not in st.session_state:
    st.session_state.chat_model = llm

if "messages" not in st.session_state:
    st.session_state.messages = []

# Style snippet to ensure iframe content inherits a transparent background
TRANSPARENT_BG_STYLE = """
<style>
    html, body {
        background-color: transparent !important;
    }
</style>
"""

def render_message(text: str) -> None:
    """Extracts and renders HTML with transparent background matching Streamlit's theme."""
    
    html_match = re.search(r'```html(.*?)```', text, re.DOTALL | re.IGNORECASE)
    
    if html_match:
        html_content = html_match.group(1).strip()
        text_without_html = re.sub(r'```html.*?```', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
        
        if text_without_html:
            st.write(text_without_html)
            
        styled_html = f"{TRANSPARENT_BG_STYLE}\n{html_content}"
        components.html(styled_html, height=800, scrolling=True)
        
    elif "<html" in text.lower() or "<div" in text.lower():
        styled_html = f"{TRANSPARENT_BG_STYLE}\n{text}"
        components.html(styled_html, height=800, scrolling=True)
        
    else:
        st.write(text)


# --- UI Header ---
st.title("المميز")
st.markdown("Tell me what's broken, or ask a follow-up question if you're stuck on a step.")
st.divider()

# --- Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_message(msg["text"]) if msg["role"] == "assistant" else st.write(msg["text"])

# --- Chat Input & Execution ---
if prompt := st.chat_input("Type your question here..."):
    # Append & display user message
    st.session_state.messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate & display AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_response = run_agent(
                prompt, 
                st.session_state.chat_model, 
                st.session_state.session_id
            )
            render_message(ai_response)
                
    # Save response to history
    st.session_state.messages.append({
        "role": "assistant", 
        "text": ai_response
    })