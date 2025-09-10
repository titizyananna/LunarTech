import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import os
from huggingface_hub import login
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import yaml
from agent import LunarTechRAGagent
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import re
import uuid
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# I will be using google/gemma-2-2b-it from Huggingface

login(new_session=False)

pipe = pipeline("text-generation", model="google/gemma-2-2b-it")
tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b-it")
model = AutoModelForCausalLM.from_pretrained("google/gemma-2-2b-it")

# Loading yaml file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
faq_path = os.path.join(BASE_DIR, "..", "data", "faq.yaml")  

faq_path = os.path.abspath(faq_path)
print("Loading FAQ from:", faq_path)

with open(faq_path, "r") as f:
    faq_data = yaml.safe_load(f)

ragent = LunarTechRAGagent(faq_data, gemma_model = model, gemma_tokenizer = tokenizer, threshhold = 0.5)

class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "..", "data", "sessions.json")
SESSION_FILE = os.path.abspath(SESSION_FILE) 

def log_interactions(session_id, question, answer):
    timestamp = datetime.utcnow().isoformat()

    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 0:
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
    else:
        sessions = {}
    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({'question': question, "answer": answer, "timestamp": timestamp})
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

    return session_id

@app.post("/api/chat")
def chat_endpoint(request: QuestionRequest):

    session_id = request.session_id or str(uuid.uuid4())
    response = ragent.answer_question(request.question)  
    answer_text = response.get("answer", "")
    cleaned_text = re.sub(r"(\*\*|\*|-)", "", answer_text).strip()
    response["answer"] = cleaned_text
    log_interactions(session_id, request.question, answer_text)

    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("""
    <h1>🚀 LunarTech CRM</h1>
    <p><a href="/chat">💬 Chat with AI Assistant</a></p>
    """)



@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    try:
        # Path to frontend folder from backend folder
        frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "new.html")
        frontend_path = os.path.abspath(frontend_path)
        
        with open(frontend_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(f"""
        <h1>❌ Chat interface not found</h1>
        <p>Looking for: {frontend_path}</p>
        <p>Please create chat.html in frontend/ folder</p>
        """)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LunarTech server...")
    print("💬 Chat: http://localhost:8000/chat")
    uvicorn.run(app, host="0.0.0.0", port=8000)