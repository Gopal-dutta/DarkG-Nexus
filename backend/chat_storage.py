import json
import os
from datetime import datetime
from typing import List, Dict, Any
import uuid

CHATS_DIR = "chats"
os.makedirs(CHATS_DIR, exist_ok=True)

def generate_chat_id():
    """Generate unique chat ID."""
    return str(uuid.uuid4())[:8]

def create_chat(title: str = None) -> str:
    """Create new chat and return chat ID."""
    chat_id = generate_chat_id()
    chat_data = {
        "id": chat_id,
        "title": title or "New Chat",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)
    
    return chat_id

def get_chat(chat_id: str) -> Dict[str, Any]:
    """Load chat by ID."""
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    if not os.path.exists(chat_path):
        return None
    
    with open(chat_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_chats() -> List[Dict[str, Any]]:
    """Get all chats (for sidebar)."""
    chats = []
    
    if not os.path.exists(CHATS_DIR):
        return chats
    
    for filename in sorted(os.listdir(CHATS_DIR), reverse=True):
        if filename.endswith(".json"):
            chat_path = os.path.join(CHATS_DIR, filename)
            with open(chat_path, "r", encoding="utf-8") as f:
                chat = json.load(f)
                chats.append({
                    "id": chat["id"],
                    "title": chat["title"],
                    "created_at": chat["created_at"],
                    "message_count": len(chat["messages"])
                })
    
    return chats

def add_message_to_chat(chat_id: str, role: str, content: str):
    """Add message to specific chat."""
    chat = get_chat(chat_id)
    
    if not chat:
        return False
    
    chat["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update title if empty or still "New Chat" and this is first user message
    if (chat["title"] == "New Chat" or chat["title"].startswith("Chat")) and role == "user":
        if len(content) > 50:
            chat["title"] = content[:50] + "..."
        else:
            chat["title"] = content
    
    # Save updated chat
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)
    
    return True

def get_chat_history(chat_id: str) -> List[Dict[str, str]]:
    """Get messages from specific chat (formatted for LLM)."""
    chat = get_chat(chat_id)
    
    if not chat:
        return []
    
    # Return last 10 messages for context window
    return chat["messages"][-10:]

def get_all_chat_messages(chat_id: str) -> List[Dict[str, str]]:
    """Get all messages from chat."""
    chat = get_chat(chat_id)
    
    if not chat:
        return []
    
    return chat["messages"]

def delete_chat(chat_id: str) -> bool:
    """Delete chat."""
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    if os.path.exists(chat_path):
        os.remove(chat_path)
        return True
    
    return False

def clear_chat_history(chat_id: str) -> bool:
    """Clear messages in chat but keep the chat."""
    chat = get_chat(chat_id)
    
    if not chat:
        return False
    
    chat["messages"] = []
    
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)
    
    return True
