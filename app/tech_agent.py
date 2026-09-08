import streamlit as st
import streamlit.components.v1 as components
import uuid
import re
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
 
from src.agent.main import run_agent
from src.agent.config import llm

print("ahmed hisham")
st.set_page_config(page_title="Your Tech Guy", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_model" not in st.session_state:
    st.session_state.chat_model = llm

if "messages" not in st.session_state:
    st.session_state.messages = []


st.title("المميز")
st.markdown("Tell me what's broken, or ask a follow-up question if you're stuck on a step.")
st.write("---")


def render_message(text):
    """Safely extracts and renders HTML, printing any normal text above it."""
    
    # 1. Look for HTML wrapped in markdown code blocks (```html ... ```)
    html_match = re.search(r'```html(.*?)```', text, re.DOTALL | re.IGNORECASE)
    
    if html_match:
        html_content = html_match.group(1).strip()
        # Remove the HTML block from the main text to find any conversational intro/outro
        text_without_html = re.sub(r'```html.*?```', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
        
        if text_without_html:
            st.write(text_without_html)
            
        # Render the HTML in an isolated iframe (height=800px) with a scrollbar
        components.html(html_content, height=800, scrolling=True)
        
    # 2. Fallback: If there are no backticks, but the text starts with HTML tags
    elif "<html" in text.lower() or "<div" in text.lower():
        components.html(text, height=800, scrolling=True)
        
    # 3. Fallback: It's just normal conversational text
    else:
        st.write(text)


# --- Render Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_message(msg["text"])
        else:
            st.write(msg["text"])


# --- Chat Input & AI Generation ---
if prompt := st.chat_input("Type your question here..."):
    
    # Add user message to screen and state
    st.session_state.messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            
            # Run the agent (Note: run_agent returns a single string now)
            ai_response = run_agent(
                prompt, 
                st.session_state.chat_model, 
                st.session_state.session_id
            )
            
            # Render the returned text/html
            render_message(ai_response)
                
    # Save the AI's response to the chat history so it survives reruns
    st.session_state.messages.append({
        "role": "assistant", 
        "text": ai_response
    })