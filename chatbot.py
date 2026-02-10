from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableMap
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader

import os
import logging
import time
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

UNIFIED_VECTOR_STORE = "./faiss_vectors/knowledge_base"


def extract_text_from_pdf(path: str):
    text = ""
    reader = PdfReader(path)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def split_text_into_chunks(text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=80000, chunk_overlap=1000)
    return splitter.split_text(text)


def create_vector_store(vector_store_path: str, text_chunks):
    new_vectors = FAISS.from_texts(text_chunks, embeddings)

    if os.path.exists(vector_store_path):
        existing = FAISS.load_local(
            vector_store_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        existing.merge_from(new_vectors)
        existing.save_local(vector_store_path)
    else:
        os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
        new_vectors.save_local(vector_store_path)


def process_transcribed_video_text(vector_store_path, input_data):
    """
    input_data: Can be a string (raw text) or a list of dicts (timestamped chunks).
    """
    if isinstance(input_data, list):
        # Timestamped chunks handling
        texts = [chunk['text'] for chunk in input_data]
        metadatas = [{"start": chunk['start'], "end": chunk['end']} for chunk in input_data]
        
        # Create/Update Vector Store with metadata
        new_vectors = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        
        if os.path.exists(vector_store_path):
            existing = FAISS.load_local(
                vector_store_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            existing.merge_from(new_vectors)
            existing.save_local(vector_store_path)
        else:
            os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
            new_vectors.save_local(vector_store_path)
            
    else:
        # Legacy String handling
        chunks = split_text_into_chunks(input_data)
        create_vector_store(vector_store_path, chunks)


def get_insights_from_video(user_query, transcribed_text=None):
    os.makedirs("./faiss_vectors", exist_ok=True)
    vector_store_path = UNIFIED_VECTOR_STORE

    if transcribed_text:
        process_transcribed_video_text(vector_store_path, transcribed_text)

    if not os.path.exists(vector_store_path):
        return {"answer": "❌ No documents found. Upload PDFs first!", "sources": []}

    vector_store = FAISS.load_local(
        vector_store_path, embeddings,
        allow_dangerous_deserialization=True
    )
    docs = vector_store.similarity_search(user_query, k=4)
    print(f"\n[RAG] Query: {user_query}")
    print(f"[RAG] Found {len(docs)} documents.")
    
    context_text = ""
    sources = []
    
    for i, doc in enumerate(docs):
        timestamp = doc.metadata.get("start", "N/A")
        content = doc.page_content
        print(f"[RAG] Doc {i+1} (Time: {timestamp}s): {content[:50]}...")
        context_text += f"\n[Time: {timestamp}s] {content}"
        
        if timestamp != "N/A":
            sources.append({"start": timestamp, "text": content[:100]})

    if not docs:
        return {"answer": "The answer is not available in the context.", "sources": []}

    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    The context includes information from video transcriptions (with timestamps) and PDF documents.
        
    If the answer is not in the provided context, ignore it.
        
    If the {question} is a greeting, say "Hey! I am here to help you with your video analysis and insights.".

    Context: {context}
    Question: {question}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    chain = prompt | llm
    response = chain.invoke({"context": context_text, "question": user_query})
    
    return {
        "answer": response.content,
        "sources": sources
    }
