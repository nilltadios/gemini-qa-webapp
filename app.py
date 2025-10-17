#!/usr/bin/env python3

"""
Gemini Multi-Agent QA System - STREAMLIT WEB VERSION
Word Count Auto-Verification with Quality Agents
"""

import os
import re
import streamlit as st
from io import BytesIO
from datetime import datetime

# PDF support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Gemini SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("ERROR: google-genai not installed! Run: pip install google-genai")
    st.stop()

# ============================================================================
# FILE READERS
# ============================================================================

def read_pdf(file_bytes):
    """Read PDF from uploaded file bytes."""
    if not PDF_SUPPORT:
        raise Exception("PyPDF2 not installed")
    text = ""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_text_file(file_bytes, encodings=['utf-8', 'latin-1', 'cp1252']):
    """Read text file with multiple encoding attempts."""
    for encoding in encodings:
        try:
            return file_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise Exception("Could not decode file")

def read_file_smart(uploaded_file):
    """Smart file reader for Streamlit uploaded files."""
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.split('.')[-1].lower()
    
    if ext == 'pdf':
        if not PDF_SUPPORT:
            return None, "PDF support not installed"
        try:
            return read_pdf(file_bytes), "PDF"
        except Exception as e:
            return None, f"PDF error: {str(e)}"
    else:
        try:
            content, encoding = read_text_file(file_bytes)
            return content, encoding
        except Exception as e:
            return None, f"Error: {str(e)}"

def strip_markdown(text):
    """Remove markdown formatting for clean text output."""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'``````', '', text)
    text = re.sub(r'^[-*]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ============================================================================
# WORD COUNTER
# ============================================================================

def count_words(text):
    """Count words, sentences, and characters for essay writing."""
    if not text or not text.strip():
        return 0, 0, 0
    
    # Word count (split by whitespace)
    words = len(text.split())
    
    # Sentence count (rough estimate)
    sentences = text.count('.') + text.count('!') + text.count('?')
    
    # Character count (excluding whitespace)
    chars = len(text.replace(' ', '').replace('\n', ''))
    
    return words, sentences, chars

# ============================================================================
# MULTI-AGENT SYSTEM WITH WORD COUNT VERIFICATION
# ============================================================================

class GeminiAssistant:
    def __init__(self):
        self.setup_api()
        self.progress_callback = None
        self.current_response = ""
        
    def setup_api(self):
        """Setup Gemini API with key from Streamlit secrets or environment."""
        # Try Streamlit secrets first, then environment variable
        api_key = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
        
        if not api_key:
            st.error("⚠️ GOOGLE_API_KEY not found! Add it to Streamlit secrets.")
            st.stop()
        
        self.client = genai.Client(api_key=api_key)
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.config_with_search = types.GenerateContentConfig(tools=[self.grounding_tool])
        self.config_no_search = types.GenerateContentConfig()
    
    def log_progress(self, message):
        """Log progress message with live callback."""
        if self.progress_callback:
            self.progress_callback(message)
    
    def quality_agent(self, prompt, use_search, conversation_history):
        """Create quality criteria including word count requirements."""
        self.log_progress("📋 Creating quality criteria (Gemini 2.5 Pro)...")
        
        config = self.config_with_search if use_search else self.config_no_search
        
        # Include conversation history in context
        history_context = ""
        if conversation_history:
            history_context = "\n\n=== CONVERSATION HISTORY ===\n"
            for msg in conversation_history:
                history_context += f"\n{msg['role'].upper()}: {msg['content']}\n"
        
        criteria_prompt = f"""Create quality criteria for this prompt.

IMPORTANT: If the prompt specifies a word count requirement (e.g., "500 words", "200-300 words", "summarize in 150 words"):
- Include a specific criterion about meeting that exact word count
- Be precise about the required word count
- Example: "Must be approximately 500 words (±10%)"

{history_context}

USER PROMPT:
{prompt}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=criteria_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            self.log_progress(f"❌ Quality agent error: {str(e)}")
            return None
    
    def grader_agent(self, response_text, criteria, use_search):
        """Grade response quality including word count verification."""
        self.log_progress("🔍 Checking quality + word count...")
        
        # Count words in response
        words, sentences, chars = count_words(response_text)
        word_count_info = f"\nACTUAL WORD COUNT: {words} words, {sentences} sentences, {chars} characters"
        
        config = self.config_with_search if use_search else self.config_no_search
        
        grader_prompt = f"""Grade this response. Reply ONLY 'pass' or 'no'.

IMPORTANT: If the criteria specify a word count requirement (e.g., "500 words", "200-300 words"):
1. Check if the actual word count matches the requirement
2. Fail the response if word count is off by more than 10%
3. Word count is the MOST IMPORTANT criterion to check

CRITERIA:
{criteria}

RESPONSE:
{response_text}

{word_count_info}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=grader_prompt,
                config=config
            )
            
            grade_result = response.text.strip().lower()
            
            # Log word count check
            if words > 0:
                self.log_progress(f"📊 Response has {words} words, {sentences} sentences")
            
            return grade_result
        except Exception as e:
            self.log_progress(f"❌ Grader error: {str(e)}")
            return "error"
    
    def refiner_agent(self, prompt, criteria, response_text, use_search, iteration, conversation_history):
        """Refine response to meet all criteria including word count."""
        self.log_progress(f"✨ Improving response (Gemini 2.5 Pro iteration {iteration})...")
        
        # Count current words
        words, _, _ = count_words(response_text)
        word_info = f"\nCurrent word count: {words} words"
        
        # Include conversation history
        history_context = ""
        if conversation_history:
            history_context = "\n\n=== CONVERSATION HISTORY ===\n"
            for msg in conversation_history:
                history_context += f"\n{msg['role'].upper()}: {msg['content']}\n"
        
        config = self.config_with_search if use_search else self.config_no_search
        
        refiner_prompt = f"""Improve this response to meet ALL criteria.

PAY SPECIAL ATTENTION to word count requirements. If criteria specify a word count:
- Expand or condense the response to meet it exactly
- Maintain quality while hitting the target word count

{word_info}

{history_context}

ORIGINAL PROMPT:
{prompt}

CRITERIA:
{criteria}

RESPONSE TO IMPROVE:
{response_text}

Provide only the improved response."""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=refiner_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            self.log_progress(f"❌ Refiner error: {str(e)}")
            return None
    
    def generate_response(self, prompt, file_contexts, use_search, use_agents, max_refinements, conversation_history=None):
        """Generate response with optional multi-agent refinement."""
        self.current_response = ""
        
        try:
            # Build conversation history context
            history_context = ""
            if conversation_history:
                history_context = "\n\n=== CONVERSATION HISTORY ===\n"
                for msg in conversation_history:
                    history_context += f"\n{msg['role'].upper()}: {msg['content']}\n"
                history_context += "\n=== END HISTORY ===\n\n"
            
            # Build full prompt with file contexts
            full_prompt = prompt
            if file_contexts:
                self.log_progress(f"📎 Loading {len(file_contexts)} file(s) into context...")
                context_section = "\n\n=== ATTACHED FILE CONTEXTS ===\n\n"
                for filename, content in file_contexts.items():
                    context_section += f"--- File: {filename} ---\n{content}\n\n"
                full_prompt = history_context + context_section + "=== USER PROMPT ===\n\n" + prompt
            else:
                full_prompt = history_context + prompt
            
            # Initial response
            search_status = "with Google Search" if use_search else "from knowledge"
            self.log_progress(f"🚀 Generating initial response {search_status}...")
            
            config = self.config_with_search if use_search else self.config_no_search
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=full_prompt,
                config=config
            )
            
            current = response.text
            self.current_response = strip_markdown(current)
            
            # If agents disabled, return immediately
            if not use_agents:
                self.log_progress("✅ Done!")
                return self.current_response
            
            # Quality agent creates criteria
            criteria = self.quality_agent(full_prompt, use_search, conversation_history or [])
            if criteria is None:
                return self.current_response
            
            # Refinement loop
            for i in range(max_refinements):
                grade = self.grader_agent(current, criteria, use_search)
                
                if "pass" in grade:
                    self.log_progress("✅ Quality + word count check passed!")
                    break
                elif "error" in grade:
                    self.log_progress("⚠️ Grader encountered an error - using current response")
                    break
                else:
                    self.log_progress(f"⚠️ Check failed - refining...")
                    new_response = self.refiner_agent(full_prompt, criteria, current, use_search, i + 1, conversation_history or [])
                    
                    if new_response is None:
                        self.log_progress("⚠️ Refinement failed - using current response")
                        break
                    
                    current = new_response
                    self.current_response = strip_markdown(current)
            else:
                self.log_progress(f"⚠️ Max iterations ({max_refinements}) reached")
            
            self.log_progress("✅ Done!")
            return self.current_response
        
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.log_progress(error_msg)
            # Return current response even on error
            if self.current_response:
                return self.current_response + f"\n\n[ERROR: {str(e)}]"
            return f"Error: {str(e)}"

# ============================================================================
# STREAMLIT WEB APP
# ============================================================================

def main():
    # Page configuration
    st.set_page_config(
        page_title="Gemini Multi-Agent QA System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
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
    .edit-button {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title
    st.title("🤖 Gemini Multi-Agent QA System")
    st.markdown("**Word Count Auto-Verification with Quality Agents - Thread Mode**")
    
    # Initialize session state
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
    
    # Sidebar - Settings and File Upload
    with st.sidebar:
        st.header("⚙️ Settings")
        
        use_search = st.checkbox("🌐 Google Search", value=True,
                                help="Enable Google Search grounding for real-time information")
        
        use_agents = st.checkbox("🤖 Quality Agents", value=True,
                                help="Enable multi-agent quality verification and word count checking")
        
        max_refinements = st.slider("Max Refinement Iterations", 1, 5, 3,
                                    help="Maximum number of refinement attempts")
        
        st.markdown("---")
        
        # Session control
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
        
        st.markdown("---")
        
        st.header("📎 File Upload")
        st.markdown("Upload files to provide context for your prompts")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['txt', 'pdf', 'md', 'py', 'json', 'csv', 'm'],
            accept_multiple_files=True,
            help="Supported: TXT, PDF, MD, PY, JSON, CSV, M"
        )
        
        # Process uploaded files
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
        
        # Display loaded files
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
    
    # Main content area
    st.markdown("---")
    
    # Display conversation thread
    if st.session_state.conversation_thread:
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
    
    # Edit mode or new prompt
    if st.session_state.edit_mode is not None:
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
                # Fork the thread: keep messages up to edit_idx, replace with edited
                st.session_state.conversation_thread = st.session_state.conversation_thread[:edit_idx]
                st.session_state.edit_mode = None
                # Add edited prompt and generate
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.conversation_thread.append({
                    'role': 'user',
                    'content': edited_prompt,
                    'timestamp': timestamp
                })
                
                # Generate response (will be handled below)
                st.session_state.generate_now = True
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.edit_mode = None
                st.rerun()
    
    else:
        # New prompt input
        st.subheader("💬 Your Prompt")
        
        prompt = st.text_area(
            "Enter your question or task:",
            height=150,
            placeholder="Example: Write a 500-word essay about renewable energy...",
            help="Be specific! Include word count requirements if needed (e.g., '300 words', 'summarize in 150 words')",
            key="new_prompt_area"
        )
        
        # Generate button
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
    
    # Process generation
    if hasattr(st.session_state, 'generate_now') and st.session_state.generate_now:
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
            progress_placeholder.text_area("Progress Log:", value=progress_text, height=200, key=f"progress_{len(st.session_state.progress_log)}")
            
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
    
    # Footer
    st.markdown("---")
    st.caption("Powered by Google Gemini 2.5 Pro | Multi-Agent Quality Verification System | Thread Mode")

if __name__ == "__main__":
    main()
