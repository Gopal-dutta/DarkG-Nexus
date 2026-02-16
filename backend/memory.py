"""
Chat history memory: stores conversation context for the current session.
Persists documents across chat sessions for RAG queries.
"""

chat_history = []

def add_message(role, content):
    """Add a message to the chat history."""
    chat_history.append({"role": role, "content": content})

def get_history():
    """Get the last 10 messages for context window."""
    return chat_history[-10:]

def get_all_history():
    """Get full chat history."""
    return chat_history

def clear_history():
    """Clear chat history."""
    global chat_history
    chat_history = []
