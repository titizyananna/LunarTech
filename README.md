# LunarTech

AI-powered lead generation system with Google Gemma model and intelligent FAQ responses.

## Features
- **AI Chat Assistant**: Powered by Google's Gemma-2-2b-it model
- **RAG System**: Intelligent FAQ retrieval and response generation
- **Session Management**: Persistent chat sessions with JSON logging
- **REST API**: FastAPI backend with CORS support
- **Real-time Responses**: Streaming AI responses for natural conversations
- **Lead Qualification**: Automated lead scoring and management



## Requirements
- Python 3.8+
- CUDA-compatible GPU (recommended) or CPU
- 8GB+ RAM recommended
- Hugging Face account
- Internet connection (downloads 5GB model first run)

## Quick Setup
1. **Clone and setup:**
   ```bash
   git clone <https://github.com/titizyananna/LunarTech.git>
   cd LunarTech
   python -m venv venv
   source venv/bin/activate 


2. **Install dependencies**
    ```bash
    pip install -r requirements.txt


3. *Hugging Face login*
    ```bash
    huggingface-cli login

Enter your token when prompted

4. **Configure environment**
    ```bash
    cp .env.example .env

5. **Run the server**
    ```bash
    python backend/main.py

## Usage
Chat interface: http://localhost:8000/chat
API request: {
  "question": "What is LunarTech?",
  "session_id": "optional-uuid"
}

# **Importat** 

The application_handler in frontend folder is just a referance its working in Apps Script. The trigger that is set on the function onFormSubmit is also in Apps Script. It works whenever someone sends a google form.


