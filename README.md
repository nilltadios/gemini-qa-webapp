# 🤖 Gemini Multi-Agent QA System

A sophisticated Streamlit web application that leverages Google's Gemini AI models with multi-agent quality verification and automatic word count checking. Built for creating high-quality, contextually-aware responses with conversation threading support.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)

## ✨ Features

### 🧵 Thread-Based Conversations
- Maintains full conversation history with context preservation
- Each message timestamped for easy tracking
- Seamless multi-turn conversations with context awareness

### ✏️ Edit & Fork
- Edit any past prompt in the conversation
- Creates a forked thread from the edited point
- Explore alternative conversation paths

### 🤖 Multi-Agent Quality System
- **Quality Agent**: Creates criteria based on your prompt requirements
- **Grader Agent**: Verifies response quality and word count accuracy
- **Refiner Agent**: Iteratively improves responses until they pass quality checks
- Automatic word count verification (±10% tolerance)

### 📊 Live Progress Streaming
- Real-time progress updates during generation
- See current response as it's being refined
- Transparent view of the agent workflow

### 🛡️ Error Resilience
- Shows partial responses even when errors occur
- Never lose work due to API failures
- Graceful degradation with informative error messages

### 📎 File Context Support
- Upload multiple files (TXT, PDF, MD, PY, JSON, CSV, M)
- Files provide context for your prompts
- Smart file reading with multiple encoding support

### 🌐 Google Search Integration
- Optional Google Search grounding for real-time information
- Get up-to-date answers with web context
- Toggle on/off based on your needs

## 📁 Project Structure

```
gemini-qa-webapp/
├── app.py              # Main Streamlit application (UI layer)
├── agents.py           # Multi-agent system (Quality, Grader, Refiner)
├── file_utils.py       # File reading utilities (PDF, TXT, etc.)
├── text_utils.py       # Text processing (word count, markdown stripping)
├── config.py           # Configuration constants
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/gemini-qa-webapp.git
cd gemini-qa-webapp
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key

Create a `.streamlit/secrets.toml` file in your project directory:

```bash
mkdir .streamlit
touch .streamlit/secrets.toml
```

Add your API key to `secrets.toml`:

```toml
GOOGLE_API_KEY = "your-api-key-here"
```

**Alternative**: Set as environment variable
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

## 🎮 Usage

### Start the Application
```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Basic Workflow

1. **Configure Settings** (Sidebar)
   - Toggle Google Search on/off
   - Enable/disable Quality Agents
   - Set max refinement iterations (1-5)

2. **Upload Files** (Optional)
   - Add context files through the sidebar
   - Supported formats: TXT, PDF, MD, PY, JSON, CSV, M

3. **Enter Your Prompt**
   - Type your question or task
   - Include word count requirements if needed (e.g., "Write a 500-word essay...")

4. **Generate Response**
   - Click "Generate Response" button
   - Watch live progress as agents work
   - See the refined response in the thread

5. **Continue Conversation**
   - Ask follow-up questions
   - Context from previous messages is preserved
   - Edit past prompts to fork new conversation paths

6. **Manage Session**
   - Clear thread to start fresh
   - View message count in sidebar

## 📚 Dependencies

- **streamlit** (>=1.28.0) - Web application framework
- **google-genai** (>=1.0.0) - Google Gemini API client
- **PyPDF2** (>=3.0.0) - PDF file reading support

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Model Names
MODEL_PRO = "gemini-2.5-pro"      # Main generation model
MODEL_FLASH = "gemini-2.5-flash"  # Fast grading model

# Agent Settings
DEFAULT_MAX_REFINEMENTS = 3        # Default refinement iterations
WORD_COUNT_TOLERANCE = 0.10        # 10% word count tolerance

# File Settings
SUPPORTED_EXTENSIONS = ['txt', 'pdf', 'md', 'py', 'json', 'csv', 'm']
TEXT_ENCODINGS = ['utf-8', 'latin-1', 'cp1252']

# UI Settings
PAGE_TITLE = "Gemini Multi-Agent QA System"
PAGE_ICON = "🤖"
```

## 🎯 Use Cases

- **Academic Writing**: Generate essays with exact word count requirements
- **Research**: Get detailed, fact-checked answers with Google Search
- **Content Creation**: Create high-quality content with automatic refinement
- **Document Analysis**: Upload files and ask questions about their content
- **Iterative Refinement**: Explore different conversation paths through editing

## 🔒 Security Notes

- Never commit your API key to version control
- Use `.streamlit/secrets.toml` for local development
- For deployment, use platform-specific secret management (Streamlit Cloud, Heroku, etc.)
- Add `.streamlit/` to your `.gitignore` file

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not found" Error
- Ensure `secrets.toml` is in the `.streamlit/` directory
- Check that the key is correctly formatted in the file
- Restart the Streamlit app after adding the key

### PDF Files Not Loading
- Install PyPDF2: `pip install PyPDF2`
- Some PDFs may have encryption or formatting issues

### Progress Not Updating
- This is normal for synchronous operations in Streamlit
- Progress updates occur after each agent completes its task

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google Gemini API](https://ai.google.dev/)
- Inspired by multi-agent AI systems and quality verification patterns

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

---

**Made with ❤️ using Google Gemini 2.5 Pro**
