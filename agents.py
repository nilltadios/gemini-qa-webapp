"""Multi-agent system for Gemini QA with quality verification."""

import os
import streamlit as st
from google import genai
from google.genai import types
from text_utils import count_words, contains_numbers
from config import MODEL_PRO, MODEL_FLASH


class GeminiAssistant:
    """Multi-agent assistant with quality verification and word count checking."""
    
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
        
        # Tools
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.code_execution_tool = types.Tool(code_execution=types.ToolCodeExecution())
        
        # Configs with different tool combinations
        self.config_with_search_and_code = types.GenerateContentConfig(
            tools=[self.grounding_tool, self.code_execution_tool]
        )
        self.config_with_search = types.GenerateContentConfig(tools=[self.grounding_tool])
        self.config_with_code = types.GenerateContentConfig(tools=[self.code_execution_tool])
        self.config_no_tools = types.GenerateContentConfig()
    
    def log_progress(self, message):
        """Log progress message with live callback."""
        if self.progress_callback:
            self.progress_callback(message)
    
    def _build_history_context(self, conversation_history):
        """Build conversation history context string."""
        if not conversation_history:
            return ""
        
        history_context = "\n\n=== CONVERSATION HISTORY ===\n"
        for msg in conversation_history:
            history_context += f"\n{msg['role'].upper()}: {msg['content']}\n"
        return history_context
    
    def _get_config(self, use_search, use_code_execution):
        """Get appropriate config based on tool requirements."""
        if use_search and use_code_execution:
            return self.config_with_search_and_code
        elif use_search:
            return self.config_with_search
        elif use_code_execution:
            return self.config_with_code
        else:
            return self.config_no_tools
    
    def quality_agent(self, prompt, use_search, conversation_history):
        """Create quality criteria including word count requirements."""
        self.log_progress(f"📋 Creating quality criteria ({MODEL_PRO})...")
        
        config = self.config_with_search if use_search else self.config_no_tools
        history_context = self._build_history_context(conversation_history)
        
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
                model=MODEL_PRO,
                contents=criteria_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            self.log_progress(f"❌ Quality agent error: {str(e)}")
            return None
    
    def grader_agent(self, response_text, criteria, use_search):
        """
        Grade response quality including word count verification.
        Uses code execution only if response contains numbers (for word counting).
        """
        self.log_progress("🔍 Checking quality + word count...")
        
        # Determine if grader should use code execution
        # Only enable code execution if response contains numbers (for accurate word counting)
        has_numbers = contains_numbers(response_text)
        use_code_execution = has_numbers
        
        if use_code_execution:
            self.log_progress("💻 Grader using code execution for numeric verification...")
        
        words, sentences, chars = count_words(response_text)
        word_count_info = f"\nACTUAL WORD COUNT: {words} words, {sentences} sentences, {chars} characters"
        
        # Get appropriate config for grader
        config = self._get_config(use_search, use_code_execution)
        
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
                model=MODEL_PRO,
                contents=grader_prompt,
                config=config
            )
            
            grade_result = response.text.strip().lower()
            
            if words > 0:
                self.log_progress(f"📊 Response has {words} words, {sentences} sentences")
            
            return grade_result
        except Exception as e:
            self.log_progress(f"❌ Grader error: {str(e)}")
            return "error"
    
    def refiner_agent(self, prompt, criteria, response_text, use_search, iteration, conversation_history):
        """Refine response to meet all criteria including word count."""
        self.log_progress(f"✨ Improving response ({MODEL_PRO} iteration {iteration})...")
        
        words, _, _ = count_words(response_text)
        word_info = f"\nCurrent word count: {words} words"
        history_context = self._build_history_context(conversation_history)
        
        config = self.config_with_search if use_search else self.config_no_tools
        
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
                model=MODEL_PRO,
                contents=refiner_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            self.log_progress(f"❌ Refiner error: {str(e)}")
            return None
    
    def generate_response(self, prompt, file_contexts, use_search, use_code_execution, 
                     use_agents, max_refinements, conversation_history=None):
        """Generate response with optional multi-agent refinement and code execution."""
        self.current_response = ""
        
        try:
            # Build full prompt
            history_context = self._build_history_context(conversation_history or [])
            
            full_prompt = prompt
            if file_contexts:
                self.log_progress(f"📎 Loading {len(file_contexts)} file(s) into context...")
                context_section = "\n\n=== ATTACHED FILE CONTEXTS ===\n\n"
                for filename, content in file_contexts.items():
                    context_section += f"--- File: {filename} ---\n{content}\n\n"
                full_prompt = history_context + context_section + "=== USER PROMPT ===\n\n" + prompt
            else:
                full_prompt = history_context + prompt
            
            # Initial response with appropriate tools
            tools_status = []
            if use_search:
                tools_status.append("Google Search")
            if use_code_execution:
                tools_status.append("Code Execution")
            
            tools_msg = f"with {' + '.join(tools_status)}" if tools_status else "from knowledge"
            self.log_progress(f"🚀 Generating initial response {tools_msg}...")
            
            config = self._get_config(use_search, use_code_execution)
            
            response = self.client.models.generate_content(
                model=MODEL_PRO,
                contents=full_prompt,
                config=config
            )
            
            # Keep original response without modification
            current = response.text
            self.current_response = current
            
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
                    new_response = self.refiner_agent(
                        full_prompt, criteria, current, use_search, i + 1, conversation_history or []
                    )
                    
                    if new_response is None:
                        self.log_progress("⚠️ Refinement failed - using current response")
                        break
                    
                    current = new_response
                    self.current_response = current
            else:
                self.log_progress(f"⚠️ Max iterations ({max_refinements}) reached")
            
            self.log_progress("✅ Done!")
            return self.current_response
        
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.log_progress(error_msg)
            if self.current_response:
                return self.current_response + f"\n\n[ERROR: {str(e)}]"
            return f"Error: {str(e)}"