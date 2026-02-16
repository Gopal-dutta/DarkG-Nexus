"""
RAG Engine: Handles document ingestion, storage, context-aware querying, AND Continuous Learning.
"""

import chromadb
import ollama
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.storage_context import StorageContext

# LOCAL embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
Settings.llm = None 

def configure_tokenizer():
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        Settings.tokenizer = encoding.encode
        print("Tokenizer configured: tiktoken cl100k_base")
    except Exception as e:
        # Fallback avoids packaged tiktoken data lookup failures
        Settings.tokenizer = lambda text: text.split()
        print(f"Tokenizer fallback in use: {e}")

configure_tokenizer()

# Initialize persistent Chroma DB
persist_dir = "chroma_data"
os.makedirs(persist_dir, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=persist_dir)
collection = chroma_client.get_or_create_collection("darkg_docs")

vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = None

def load_index():
    global index
    try:
        if collection.count() > 0:
            print("Loading index from vector store...")
            index = VectorStoreIndex.from_vector_store(vector_store)
            print("Index loaded successfully")
            return True
    except Exception as e:
        print(f"Could not load index: {e}")
    return False

def ingest_documents(folder="uploaded_docs"):
    global index
    if not os.path.exists(folder):
        return False, "Upload folder does not exist"
    try:
        print("Loading documents...")
        documents = SimpleDirectoryReader(folder).load_data()
        if not documents:
            return False, "No readable documents found"
        
        print("Indexing documents...")
        if index is None:
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        else:
            for doc in documents:
                index.insert(doc)
        return True, None
    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)

# === NEW: CONTINUOUS LEARNING ===
def learn_from_chat(user_query, ai_response):
    """
    Takes the user query and AI response, turns them into a 'Document',
    and inserts them into the Vector DB. The AI will 'remember' this next time.
    """
    global index
    try:
        # Create a text blob representing the knowledge gained
        knowledge_text = f"User asked: {user_query}\nAnswer: {ai_response}"
        
        # Create a Document object
        new_doc = Document(text=knowledge_text, metadata={"source": "chat_memory", "type": "learned_knowledge"})
        
        # Insert into index
        if index is None:
            # If no index exists, create one with this memory
            index = VectorStoreIndex.from_documents([new_doc], storage_context=storage_context)
        else:
            index.insert(new_doc)
            
        print(f"✅ Learned new information from chat.")
        return True
    except Exception as e:
        print(f"❌ Failed to learn: {e}")
        return False

def has_documents():
    return collection.count() > 0

def query_docs(question: str):
    global index
    if index is None: load_index()
    if index is None: return "No documents indexed."
    
    try:
        print("Retrieving context...")
        # UPGRADE: Increased top_k to 20 to read more pages of the book
        retriever = index.as_retriever(similarity_top_k=20)
        nodes = retriever.retrieve(question)
        
        context_text = "\n\n".join([n.node.get_text() for n in nodes])
        
        # Limit context size to prevent crashing 4GB VRAM
        # (Approx 12,000 characters is safe for Llama 3.2 context window)
        if len(context_text) > 12000:
            context_text = context_text[:12000]
            print("Truncated context to fit memory.")

    except Exception as e:
        context_text = f"Error retrieving context: {str(e)}"
    
    try:
        print("Calling Ollama...")
        system_prompt = """You are DarkG Nexus, an elite intelligent analyst.
        
        **INSTRUCTIONS:**
        1. **Deep Analysis:** Analyze the provided Document Context (which includes Book excerpts AND past Chat Memories).
        2. **Comprehensive:** If the context is from a book, cover ALL topics mentioned. Do not summarize briefly.
        3. **Structure:** Use **Bold**, ### Headers, and | Tables |.
        4. **Memory:** If the context contains 'User asked', this is your past memory. Use it to answer better.
        """

        response = ollama.chat(
            model="llama3.2", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error generating response: {str(e)}"

def reset_index():
    global index, collection, vector_store, storage_context
    try:
        chroma_client.delete_collection("darkg_docs")
        collection = chroma_client.get_or_create_collection("darkg_docs")
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = None
        return True
    except Exception as e:
        return False

load_index()