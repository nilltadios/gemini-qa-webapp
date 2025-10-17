#!/usr/bin/env python3

"""
Gemini Multi-Agent QA System - STREAMLIT WEB VERSION
Word Count Auto-Verification with Quality Agents - Thread Mode
"""

import streamlit as st
from datetime import datetime
from agents import GeminiAssistant
from file_utils import read_file_smart
from text_utils import count_words
from config import (
    PAGE_TITLE, PAGE_ICON, SUPPORTED_EXTENSIONS,
    DEFAULT_MAX_REFINEMENTS
)


def init_session_state():
    """Initialize all session state variables."""
    if 'file_contexts' not in st.session_state:
        st.session_state.file_contexts = {}
    if 'assistant' not in st.session_state:
        st.session_state.assistant = GeminiAssistant()
    if 'conversation_thread' not in st.session_state:
        st.session_state.conversation_thread = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = None
    if 'progress_log' not in st.session_state:
        st.session_state.progress_log = []


def render_sidebar():
    """Render sidebar with settings and file upload."""
    with st.sidebar:
        st.header("⚙️ Settings")

        use_search = st.checkbox("🌐 Google Search", value=True,
                                help="Enable Google Search grounding for real-time information")

        use_code_execution = st.checkbox("💻 Code Execution", value=True,
                                help="Enable Python code generation and execution for calculations")

        use_agents = st.checkbox("🤖 Quality Agents", value=True,
                                help="Enable multi-agent quality verification and word count checking")

        max_refinements = st.slider("Max Refinement Iterations", 1, 5, DEFAULT_MAX_REFINEMENTS,
                                    help="Maximum number of refinement attempts")

        st.markdown("---")
        render_session_control()
        st.markdown("---")
        render_file_upload()

        return use_search, use_code_execution, use_agents, max_refinements


def render_session_control():
    """Render session control section."""
    st.header("🔄 Session Control")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Thread", use_container_width=True):
            st.session_state.conversation_thread = []
            st.session_state.edit_mode = None
            st.session_state.progress_log = []
            st.success("Thread cleared!")
            st.rerun()

    with col2:
        thread_count = len(st.session_state.conversation_thread)
        st.metric("Messages", thread_count)


def render_file_upload():
    """Render file upload section."""
    st.header("📎 File Upload")
    st.markdown("Upload files to provide context for your prompts")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=SUPPORTED_EXTENSIONS,
        accept_multiple_files=True,
        help=f"Supported: {', '.join(SUPPORTED_EXTENSIONS).upper()}"
    )

    if uploaded_files:
        new_files = {}
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.file_contexts:
                content, file_type = read_file_smart(uploaded_file)
                if content is None:
                    st.error(f"❌ {uploaded_file.name}: {file_type}")
                else:
                    new_files[uploaded_file.name] = content
                    st.session_state.file_contexts[uploaded_file.name] = content

        if new_files:
            st.success(f"✅ Loaded {len(new_files)} new file(s)")

    render_loaded_files()


def render_loaded_files():
    """Render loaded files list."""
    if st.session_state.file_contexts:
        st.markdown("---")
        st.subheader("📚 Loaded Files")
        for filename, content in st.session_state.file_contexts.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"📄 {filename}")
                st.caption(f"{len(content)} characters")
            with col2:
                if st.button("🗑️", key=f"remove_{filename}"):
                    del st.session_state.file_contexts[filename]
                    st.rerun()

        if st.button("🗑️ Clear All Files", type="secondary"):
            st.session_state.file_contexts = {}
            st.rerun()

        total_chars = sum(len(c) for c in st.session_state.file_contexts.values())
        st.info(f"📊 Total: {len(st.session_state.file_contexts)} files, {total_chars:,} characters")


def render_conversation_thread():
    """Render the conversation thread."""
    if not st.session_state.conversation_thread:
        return

    st.subheader("💬 Conversation Thread")

    for idx, message in enumerate(st.session_state.conversation_thread):
        timestamp = message.get('timestamp', '')

        if message['role'] == 'user':
            with st.container():
                st.markdown(f'<div class="chat-message user-message">', unsafe_allow_html=True)
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"**👤 You** *({timestamp})*")
                    st.markdown(message['content'])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{idx}", help="Edit and fork this message"):
                        st.session_state.edit_mode = idx
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f'<div class="chat-message assistant-message">', unsafe_allow_html=True)
                st.markdown(f"**🤖 Assistant** *({timestamp})*")
                st.markdown(message['content'])

                # Word count statistics
                words, sentences, chars = count_words(message['content'])
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"📝 {words} words")
                with col2:
                    st.caption(f"📄 {sentences} sentences")
                with col3:
                    st.caption(f"🔤 {chars} characters")

                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")


def render_edit_mode():
    """Render edit mode interface."""
    if st.session_state.edit_mode is None:
        return False

    st.subheader("✏️ Edit Prompt (Fork Thread)")
    edit_idx = st.session_state.edit_mode
    original_prompt = st.session_state.conversation_thread[edit_idx]['content']

    st.info(f"Editing message #{edit_idx + 1}. The thread will be forked from this point.")

    edited_prompt = st.text_area(
        "Edit your prompt:",
        value=original_prompt,
        height=150,
        key="edit_prompt_area"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Save & Generate", type="primary", use_container_width=True):
            st.session_state.conversation_thread = st.session_state.conversation_thread[:edit_idx]
            st.session_state.edit_mode = None
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.conversation_thread.append({
                'role': 'user',
                'content': edited_prompt,
                'timestamp': timestamp
            })
            st.session_state.generate_now = True
            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.edit_mode = None
            st.rerun()

    return True


def render_prompt_input():
    """Render new prompt input interface."""
    st.subheader("💬 Your Prompt")

    prompt = st.text_area(
        "Enter your question or task:",
        height=150,
        placeholder="Example: Write a 500-word essay about renewable energy...",
        help="Be specific! Include word count requirements if needed (e.g., '300 words', 'summarize in 150 words')",
        key="new_prompt_area"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("✨ GENERATE RESPONSE ✨", type="primary", use_container_width=True)

    if generate_button and prompt.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.conversation_thread.append({
            'role': 'user',
            'content': prompt,
            'timestamp': timestamp
        })
        st.session_state.generate_now = True
        st.rerun()


def process_generation(use_search, use_code_execution, use_agents, max_refinements):
    """Process response generation with live progress."""
    if not hasattr(st.session_state, 'generate_now') or not st.session_state.generate_now:
        return

    st.session_state.generate_now = False

    # Get the last user message
    last_user_msg = [msg for msg in st.session_state.conversation_thread if msg['role'] == 'user'][-1]
    prompt = last_user_msg['content']

    # Create progress container
    st.markdown("---")
    st.subheader("🔄 Processing...")

    progress_placeholder = st.empty()
    response_placeholder = st.empty()

    # Setup live progress callback
    st.session_state.progress_log = []

    def progress_callback(message):
        st.session_state.progress_log.append(message)
        progress_text = "\n".join(st.session_state.progress_log)
        progress_placeholder.text_area("Progress Log:", value=progress_text, height=200, 
                                      key=f"progress_{len(st.session_state.progress_log)}")

        # Show current response if available
        if st.session_state.assistant.current_response:
            with response_placeholder.container():
                st.markdown("### 📝 Current Response")
                st.markdown(st.session_state.assistant.current_response)

    st.session_state.assistant.progress_callback = progress_callback

    # Build conversation history (excluding current prompt)
    conversation_history = [msg for msg in st.session_state.conversation_thread[:-1]]

    # Generate response
    try:
        response = st.session_state.assistant.generate_response(
            prompt=prompt,
            file_contexts=st.session_state.file_contexts,
            use_search=use_search,
            use_code_execution=use_code_execution,
            use_agents=use_agents,
            max_refinements=max_refinements,
            conversation_history=conversation_history
        )

        # Add response to thread
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.conversation_thread.append({
            'role': 'assistant',
            'content': response,
            'timestamp': timestamp
        })

        st.success("✅ Generation complete!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during generation: {str(e)}")
        # Still add partial response if available
        if st.session_state.assistant.current_response:
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.conversation_thread.append({
                'role': 'assistant',
                'content': st.session_state.assistant.current_response + f"\n\n[ERROR: {str(e)}]",
                'timestamp': timestamp
            })
            st.rerun()


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # Title
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.markdown("**Word Count Auto-Verification with Quality Agents - Thread Mode**")

    # Initialize session state
    init_session_state()

    # Render sidebar and get settings
    use_search, use_code_execution, use_agents, max_refinements = render_sidebar()

    # Main content
    st.markdown("---")
    render_conversation_thread()

    # Edit mode or new prompt
    if not render_edit_mode():
        render_prompt_input()

    # Process generation if needed
    process_generation(use_search, use_code_execution, use_agents, max_refinements)

    # Footer
    st.markdown("---")
    st.caption("Powered by Google Gemini 2.5 Pro | Multi-Agent Quality Verification System | Thread Mode | Updated Oct,17 2025 7:44 PM")


if __name__ == "__main__":
    main()
