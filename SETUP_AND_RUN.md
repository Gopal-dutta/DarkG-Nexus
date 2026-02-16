# DarkG Nexus - Setup & Run Guide

## Prerequisites
- **Ollama** installed and downloaded on Windows ([ollama.ai](https://ollama.ai))
- **Python 3.11+** installed
- **Node.js** installed (for Electron desktop app)
- **Llama-3 model** downloaded in Ollama (`ollama pull llama2` or `ollama pull llama2:13b`)

---

## Step 1: Start Ollama (Terminal 1)

```powershell
ollama serve
```

**Expected Output:**
```
listening on 127.0.0.1:11434
```

Leave this terminal running (this is your AI engine).

---

## Step 2: Start FastAPI Backend (Terminal 2)

```powershell
cd D:\DarkG-Nexus\backend
python -m uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

The backend is now ready at **http://127.0.0.1:8000**

---

## Step 3: Start Electron Desktop App (Terminal 3)

```powershell
cd D:\DarkG-Nexus\desktop-app
npm start
```

**Expected Output:**
```
> electron .
```

The desktop app window opens automatically. You're now ready to use DarkG Nexus!

---

## How to Use

### 1. Upload Documents
- Click the **"+"** button at the bottom
- Select PDF, DOCX, or TXT files (100+ pages supported)
- Wait for indexing (documents appear in status bar)

### 2. Ask Questions
- Type your question in the text field
- Press **Enter** or click the send arrow
- AI responds based on your documents

### 3. Chat History
- All messages are saved in the current session
- Switch between document Q&A and general chat
- Upload new documents anytime to change context

### 4. Clear Data
- **Clear Documents**: Backend menu → /clear-documents endpoint
- **Clear History**: Backend menu → /clear-history endpoint

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" on app startup | Ensure Ollama and FastAPI are running |
| App says "No LLM available" | Check Terminal 1 (Ollama must be running) |
| Upload fails | Use .pdf, .docx, or .txt files only |
| Slow first response | First API call loads embedding model (~10s) - this is normal |
| Documents not saved after restart | Restart FastAPI backend (Terminal 2) to reload ChromaDB |

---

## Endpoints (For Advanced Users)

Access all endpoints at **http://127.0.0.1:8000/docs**

- `POST /chat` - Send message with context
- `POST /upload` - Upload documents
- `GET /documents` - List uploaded files
- `POST /clear-documents` - Delete all documents
- `GET /history` - Get chat history
- `POST /clear-history` - Clear messages
- `GET /health` - System status

---

## Stop Everything

Press **Ctrl+C** in each terminal to stop:
1. Terminal 1 (Ollama) - Stop LLM engine
2. Terminal 2 (FastAPI) - Stop backend
3. Terminal 3 (Electron) - Close app window or Ctrl+C

That's it! You have a fully functional personal AI assistant.
