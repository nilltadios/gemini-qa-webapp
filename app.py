#!/usr/bin/env python3

"""
Gemini Multi-Agent QA System - STREAMLIT WEB VERSION
Word Count Auto-Verification with Quality Agents
"""

import os
import re
import streamlit as st
from io import BytesIO

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
    text = re.sub(r'```[\s\S]*?```', '', text)
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
        self.progress_messages = []

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
        """Log progress message."""
        self.progress_messages.append(message)

    def quality_agent(self, prompt, use_search):
        """Create quality criteria including word count requirements."""
        self.log_progress("📋 Creating quality criteria (Gemini 2.5 Pro)...")

        config = self.config_with_search if use_search else self.config_no_search

        criteria_prompt = f"""Create quality criteria for this prompt.

IMPORTANT: If the prompt specifies a word count requirement (e.g., "500 words", "200-300 words", "summarize in 150 words"):
- Include a specific criterion about meeting that exact word count
- Be precise about the required word count
- Example: "Must be approximately 500 words (±10%)"

USER PROMPT:
{prompt}
"""

        response = self.client.models.generate_content(
            model='gemini-2.5-pro',
            contents=criteria_prompt,
            config=config
        )

        return response.text

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

    def refiner_agent(self, prompt, criteria, response_text, use_search, iteration):
        """Refine response to meet all criteria including word count."""
        self.log_progress(f"✨ Improving response (Gemini 2.5 Pro iteration {iteration})...")

        # Count current words
        words, _, _ = count_words(response_text)
        word_info = f"\nCurrent word count: {words} words"

        config = self.config_with_search if use_search else self.config_no_search

        refiner_prompt = f"""Improve this response to meet ALL criteria.

PAY SPECIAL ATTENTION to word count requirements. If criteria specify a word count:
- Expand or condense the response to meet it exactly
- Maintain quality while hitting the target word count

{word_info}

ORIGINAL PROMPT:
{prompt}

CRITERIA:
{criteria}

RESPONSE TO IMPROVE:
{response_text}

Provide only the improved response."""

        response = self.client.models.generate_content(
            model='gemini-2.5-pro',
            contents=refiner_prompt,
            config=config
        )

        return response.text

    def generate_response(self, prompt, file_contexts, use_search, use_agents, max_refinements):
        """Generate response with optional multi-agent refinement."""
        try:
            self.progress_messages = []

            # Build full prompt with file contexts
            full_prompt = prompt
            if file_contexts:
                self.log_progress(f"📎 Loading {len(file_contexts)} file(s) into context...")
                context_section = "\n\n=== ATTACHED FILE CONTEXTS ===\n\n"
                for filename, content in file_contexts.items():
                    context_section += f"--- File: {filename} ---\n{content}\n\n"
                full_prompt = context_section + "=== USER PROMPT ===\n\n" + prompt

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

            # If agents disabled, return immediately
            if not use_agents:
                self.log_progress("✅ Done!")
                return strip_markdown(current)

            # Quality agent creates criteria
            criteria = self.quality_agent(full_prompt, use_search)
            if criteria is None:
                return strip_markdown(current)

            # Refinement loop
            for i in range(max_refinements):
                grade = self.grader_agent(current, criteria, use_search)

                if "pass" in grade:
                    self.log_progress("✅ Quality + word count check passed!")
                    break
                else:
                    self.log_progress(f"⚠️ Check failed - refining...")
                    new_response = self.refiner_agent(full_prompt, criteria, current, use_search, i + 1)
                    if new_response is None:
                        break
                    current = new_response
            else:
                self.log_progress(f"⚠️ Max iterations ({max_refinements}) reached")

            self.log_progress("✅ Done!")
            return strip_markdown(current)

        except Exception as e:
            self.log_progress(f"❌ Error: {str(e)}")
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
        .big-font {
            font-size: 20px !important;
            font-weight: bold;
        }
        .stTextArea textarea {
            font-size: 16px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title
    st.title("🤖 Gemini Multi-Agent QA System")
    st.markdown("**Word Count Auto-Verification with Quality Agents**")

    # Initialize session state
    if 'file_contexts' not in st.session_state:
        st.session_state.file_contexts = {}
    if 'assistant' not in st.session_state:
        st.session_state.assistant = GeminiAssistant()
    if 'response' not in st.session_state:
        st.session_state.response = ""

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

    # Prompt input
    st.subheader("💬 Your Prompt")
    prompt = st.text_area(
        "Enter your question or task:",
        height=200,
        placeholder="Example: Write a 500-word essay about renewable energy...",
        help="Be specific! Include word count requirements if needed (e.g., '300 words', 'summarize in 150 words')"
    )

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("✨ GENERATE RESPONSE ✨", type="primary", use_container_width=True)

    # Process generation
    if generate_button:
        if not prompt.strip():
            st.warning("⚠️ Please enter a prompt!")
        else:
            # Create progress container
            progress_container = st.container()
            with progress_container:
                st.markdown("---")
                st.subheader("🔄 Processing...")
                progress_placeholder = st.empty()

                # Show initial status
                with st.spinner("Generating response..."):
                    # Generate response
                    response = st.session_state.assistant.generate_response(
                        prompt=prompt,
                        file_contexts=st.session_state.file_contexts,
                        use_search=use_search,
                        use_agents=use_agents,
                        max_refinements=max_refinements
                    )

                    # Display progress messages
                    progress_text = "\n".join(st.session_state.assistant.progress_messages)
                    progress_placeholder.text_area("Progress Log:", value=progress_text, height=200)

                    # Store response
                    st.session_state.response = response

            st.success("✅ Generation complete!")

    # Display response
    if st.session_state.response:
        st.markdown("---")
        st.subheader("📝 Response")

        # Display the response
        st.markdown(st.session_state.response)

        # Word count statistics
        words, sentences, chars = count_words(st.session_state.response)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Words", f"{words:,}")
        with col2:
            st.metric("📄 Sentences", f"{sentences:,}")
        with col3:
            st.metric("🔤 Characters", f"{chars:,}")
        with col4:
            st.metric("📁 Files Used", len(st.session_state.file_contexts))

        # Copy button (download as text)
        st.download_button(
            label="📥 Download Response",
            data=st.session_state.response,
            file_name="gemini_response.txt",
            mime="text/plain"
        )

    # Footer
    st.markdown("---")
    st.caption("Powered by Google Gemini 2.5 Pro | Multi-Agent Quality Verification System")

if __name__ == "__main__":
    main()
