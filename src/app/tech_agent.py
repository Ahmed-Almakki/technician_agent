import streamlit as st
import uuid

from src.agent.main import run_agent
from src.agent.config import llm

# --- Page Config ---
# We use "wide" layout here so the text and images have plenty of room side-by-side
st.set_page_config(page_title="Your Tech Guy", layout="wide")

# --- Initialize Session State ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_model" not in st.session_state:
    st.session_state.chat_model = llm

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Header ---
st.title("Your Tech Guy")
st.markdown("Tell me what's broken, or ask a follow-up question if you're stuck on a step.")
st.write("---")


# --- Helper Function to Render Steps ---
def render_repair_steps(steps_data):
    """Renders the steps and images side-by-side."""
    for idx, section in enumerate(steps_data, 1):
        title = section.get("title", "")
        if not title.strip():
            title = f"Step {idx} (Continued)"
            
        st.markdown(f"### {title}")
        
        steps_list = section.get("steps", [])
        images_list = section.get("images", [])
        
        # If the step has images, split the screen 60% text / 40% images
        if images_list:
            text_col, img_col = st.columns([0.6, 0.4], gap="large")
            
            with text_col:
                for step_text in steps_list:
                    st.markdown(f"- {step_text}")
                    
            with img_col:
                # If there are multiple images for one step, stack them neatly or put them side-by-side
                if len(images_list) > 1:
                    sub_cols = st.columns(len(images_list))
                    for col, img_url in zip(sub_cols, images_list):
                        col.image(img_url, use_container_width=True)
                else:
                    st.image(images_list[0], use_container_width=True)
                    
        # If there are no images, just show the text across the full width
        else:
            for step_text in steps_list:
                st.markdown(f"- {step_text}")
                
        st.divider() # Adds a clean line between each major step


# --- Render Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 1. Print the conversational text
        if msg.get("text"):
            st.write(msg["text"])
            
        # 2. Render the steps side-by-side if they exist
        if msg.get("steps"):
            render_repair_steps(msg["steps"])


# --- Chat Input & AI Generation ---
if prompt := st.chat_input("Type your question here..."):
    
    # Add user message to screen and state
    st.session_state.messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        # Very clean, professional loading state with no emojis
        with st.spinner("Thinking..."):
            
            # Run the agent
            ai_text, ai_steps = run_agent(
                prompt, 
                st.session_state.chat_model, 
                st.session_state.session_id
            )
            
            # Show the conversational text
            st.write(ai_text)
            
            # Show the side-by-side steps
            if ai_steps:
                render_repair_steps(ai_steps)
                
    # Save the AI's response to the chat history so it survives reruns
    st.session_state.messages.append({
        "role": "assistant", 
        "text": ai_text, 
        "steps": ai_steps
    })