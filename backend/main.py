from fastapi import FastAPI, UploadFile, File, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import shutil
import os
import uuid
import re
import time # Added for file handling

# ReportLab for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from memory import add_message, get_history, clear_history, get_all_history
from rag_engine import ingest_documents, query_docs, has_documents, reset_index, learn_from_chat
from chat_storage import (
    create_chat, get_chat, get_all_chats, add_message_to_chat,
    get_chat_history, delete_chat, clear_chat_history, get_all_chat_messages
)

app = FastAPI(title="DarkG Nexus")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    chat_id: str = None 

UPLOAD_DIR = "uploaded_docs"
GENERATED_DIR = "generated_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        chat_id = request.chat_id
        if not chat_id: chat_id = create_chat()
        
        # 1. DETECT PDF INTENT
        triggers = ["pdf", "download", "document format"]
        wants_pdf = any(t in request.message.lower() for t in triggers)
        
        add_message_to_chat(chat_id, "user", request.message)
        
        chat_history = get_chat_history(chat_id)
        formatted_history = []
        for msg in chat_history:
            formatted_history.append({"role": msg["role"], "content": msg["content"]})

        if has_documents():
            answer = query_docs(request.message)
        else:
            formatted_history.insert(0, {
                "role": "system",
                "content": "You are DarkG Nexus. Be detailed, structured (Tables/Bold), and precise."
            })
            try:
                response = ollama.chat(model="llama3.2", messages=formatted_history)
                answer = response["message"]["content"]
            except Exception as e:
                answer = f"Error from LLM: {str(e)}"

        add_message_to_chat(chat_id, "assistant", answer)
        learn_from_chat(request.message, answer)
        
        return {"response": answer, "chat_id": chat_id, "can_download_pdf": wants_pdf}
    except Exception as e:
        return {"response": str(e), "chat_id": chat_id, "error": True}


@app.post("/generate-pdf")
def generate_pdf(content: str = Form(...)):
    try:
        # Clean Content for PDF (Remove Emojis/Special Chars)
        content = content.encode('ascii', 'ignore').decode('ascii')
        
        clean_text = re.sub(r'[^\w\s]', '', content)
        words = clean_text.split()[:5]
        if not words: words = ["DarkG_Response"]
        filename = "_".join(words) + ".pdf"
        filepath = os.path.join(GENERATED_DIR, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("DarkG Nexus Response", styles['Title']))
        story.append(Spacer(1, 12))
        
        normal_style = styles['BodyText']
        code_style = ParagraphStyle('Code', parent=styles['Code'], backColor=colors.lightgrey, fontSize=8, leading=10)
        
        lines = content.split('\n')
        in_code = False
        code_buffer = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("```"):
                if in_code: 
                    full_code = "\n".join(code_buffer).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Preformatted(full_code, code_style))
                    story.append(Spacer(1, 12))
                    code_buffer = []
                    in_code = False
                else: 
                    in_code = True
                continue
                
            if in_code:
                code_buffer.append(line)
            else:
                if line.startswith("###"):
                    text = line.replace("#", "").strip()
                    story.append(Paragraph(text, styles['Heading2']))
                elif line:
                    line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
                    line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(line, normal_style))
                    story.append(Spacer(1, 6))

        doc.build(story)
        
        with open(filepath, "rb") as f:
            file_bytes = f.read()
            
        try: os.remove(filepath)
        except: pass

        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(e)
        return Response(content=f"Error: {str(e)}", status_code=500)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Robust Upload: Handles locked files and overwrites properly."""
    try:
        print(f"\n=== UPLOAD START: {file.filename} ===")
        
        # 1. Try to clean up old files, but DON'T crash if locked
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path) # Try delete
                        print(f"Deleted old file: {filename}")
                except Exception as e:
                    print(f"Skipping locked file {filename}: {e}")
                    # We continue even if delete fails. 
                    # We will simply overwrite or ignore it.

        # 2. Save the new file
        # If the file already exists and is locked, we modify the name slightly
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Check if target is locked by trying to open it
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            # If locked, save as a new name
            save_path = os.path.join(UPLOAD_DIR, f"new_{file.filename}")
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        print(f"File saved to: {save_path}")
        
        # 3. Reset Index (Important to clear old document memory)
        print("Resetting Vector Index...")
        reset_index()
        
        # 4. Ingest
        print("Starting ingestion...")
        ingest_documents(UPLOAD_DIR)
        
        return {"status": "uploaded and indexed", "filename": file.filename}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# === KEEP EXISTING ENDPOINTS ===
@app.post("/chats/new")
def new_chat(title: str = None):
    chat_id = create_chat(title or "New Chat")
    return {"chat_id": chat_id, "title": "New Chat"}

@app.get("/chats")
def list_chats():
    return {"chats": get_all_chats()}

@app.get("/chats/{chat_id}")
def load_chat(chat_id: str):
    chat = get_chat(chat_id)
    if not chat: return {"status": "error", "message": "Chat not found"}
    messages = get_all_chat_messages(chat_id)
    formatted_messages = []
    for m in messages:
         formatted_messages.append({"content": m.get("content"), "role": m.get("role"), "showPdfBtn": False})
    return {"chat_id": chat_id, "title": chat["title"], "messages": formatted_messages}

@app.delete("/chats/{chat_id}")
def delete_specific_chat(chat_id: str):
    if delete_chat(chat_id): return {"status": "deleted"}
    return {"status": "error"}

@app.post("/chats/{chat_id}/clear")
def clear_specific_chat_history(chat_id: str):
    if clear_chat_history(chat_id): return {"status": "cleared"}
    return {"status": "error"}

@app.get("/documents")
def get_documents():
    docs = []
    if os.path.exists(UPLOAD_DIR):
        docs = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.pdf', '.docx', '.txt'))]
    return {"documents": docs}

@app.post("/clear-documents")
def clear_documents():
    try:
        if os.path.exists(UPLOAD_DIR):
            for f in os.listdir(UPLOAD_DIR):
                try: os.remove(os.path.join(UPLOAD_DIR, f))
                except: pass
        reset_index()
        return {"status": "documents cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}