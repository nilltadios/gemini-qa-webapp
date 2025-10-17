# Gemini Multi-Agent QA System - Web App

A powerful AI assistant powered by Google Gemini 2.5 with multi-agent quality verification and automatic word count validation.

## Features

- 🤖 Multi-agent quality verification system
- 📊 Automatic word count verification
- 🌐 Google Search integration for real-time information
- 📎 Support for multiple file formats (TXT, PDF, MD, PY, JSON, CSV)
- ✨ Iterative refinement for high-quality responses
- 📝 Real-time word, sentence, and character counting

## Installation

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Google API key:
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Add to Streamlit secrets: Create `.streamlit/secrets.toml` with:
   ```toml
   GOOGLE_API_KEY = "your_api_key_here"
   ```
   - Or set environment variable:
   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   ```

3. Run the app:
```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository, branch (main), and main file (app.py)
   - Click "Advanced settings" → "Secrets"
   - Add your API key:
     ```
     GOOGLE_API_KEY = "your_api_key_here"
     ```
   - Click "Deploy"

3. **Your app will be live at:** `https://your-app-name.streamlit.app`

## Usage

1. **Enter your prompt** in the text area
2. **Upload files** (optional) via the sidebar to provide context
3. **Configure settings:**
   - Toggle Google Search for real-time information
   - Enable/disable Quality Agents for verification
   - Adjust max refinement iterations
4. **Click "Generate Response"** and wait for results
5. **View statistics** including word count, sentences, and characters
6. **Download your response** as a text file

## How It Works

### Multi-Agent System

1. **Generator Agent** (Gemini 2.5 Flash): Creates initial response
2. **Quality Agent** (Gemini 2.5 Pro): Defines quality criteria including word count requirements
3. **Grader Agent** (Gemini 2.5 Flash): Evaluates response quality and word count accuracy
4. **Refiner Agent** (Gemini 2.5 Pro): Improves response until it meets all criteria

### Word Count Verification

The system automatically detects word count requirements in your prompt (e.g., "500 words", "200-300 words") and ensures the response meets those requirements within ±10% tolerance.

## Updating Your App

After deploying, updates are automatic:

```bash
# Make changes to app.py
git add .
git commit -m "Update feature"
git push origin main
```

Your app will automatically update within 1-2 minutes!

## Troubleshooting

- **API Key Error:** Ensure your GOOGLE_API_KEY is set correctly in Streamlit secrets
- **PDF Not Loading:** Verify PyPDF2 is installed: `pip install PyPDF2`
- **Slow Performance:** Consider disabling Google Search or reducing max refinements

## Tech Stack

- **Framework:** Streamlit
- **AI Model:** Google Gemini 2.5 (Pro & Flash)
- **Language:** Python 3.8+
- **File Support:** PyPDF2 for PDF processing

## License

MIT License
