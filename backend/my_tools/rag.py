from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, Optional, Callable

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings


class RAGManager:
    """Manages RAG (Retrieval Augmented Generation) functionality for PDF documents."""
    
    def __init__(self, embeddings: GoogleGenerativeAIEmbeddings):
        """
        Initialize RAG Manager with embeddings model.
        
        Args:
            embeddings: Embeddings model for vectorization
        """
        self.embeddings = embeddings
        self._thread_retrievers: Dict[str, Any] = {}
        self._thread_metadata: Dict[str, dict] = {}
    
    def _get_retriever(self, thread_id: Optional[str]) -> Optional[Any]:
        """Fetch the retriever for a thread if available."""
        if thread_id and thread_id in self._thread_retrievers:
            return self._thread_retrievers[thread_id]
        return None
    
    def ingest_pdf(self, file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
        """
        Build a FAISS retriever for the uploaded PDF and store it for the thread.
        
        Args:
            file_bytes: PDF file bytes
            thread_id: Unique identifier for the chat thread
            filename: Original filename (optional)
            
        Returns:
            dict: Summary information about the ingested document
        """
        if not file_bytes:
            raise ValueError("No bytes received for ingestion.")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        try:
            loader = PyPDFLoader(temp_path)
            docs = loader.load()
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
            )
            chunks = splitter.split_documents(docs)
            
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            retriever = vector_store.as_retriever(
                search_type="similarity", search_kwargs={"k": 4}
            )
            
            self._thread_retrievers[str(thread_id)] = retriever
            self._thread_metadata[str(thread_id)] = {
                "filename": filename or os.path.basename(temp_path),
                "documents": len(docs),
                "chunks": len(chunks),
            }
            
            return {
                "filename": filename or os.path.basename(temp_path),
                "documents": len(docs),
                "chunks": len(chunks),
            }
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
    
    def create_rag_tool(self, thread_id: Optional[str] = None) -> Callable:
        """
        Create a RAG tool function for the given thread.
        
        Args:
            thread_id: Thread ID for context
            
        Returns:
            Callable: RAG tool function
        """
        @tool
        def rag_tool(query: str) -> dict:
            """
            Retrieve relevant information from the uploaded PDF for this chat thread.
            """
            retriever = self._get_retriever(thread_id)
            if retriever is None:
                return {
                    "error": "No document indexed for this chat. Upload a PDF first.",
                    "query": query,
                }
            
            result = retriever.invoke(query)
            context = [doc.page_content for doc in result]
            metadata = [doc.metadata for doc in result]
            
            return {
                "query": query,
                "context": context,
                "metadata": metadata,
                "source_file": self._thread_metadata.get(str(thread_id), {}).get("filename"),
            }
        
        return rag_tool
    
    def thread_has_document(self, thread_id: str) -> bool:
        """Check if a thread has an associated document."""
        return str(thread_id) in self._thread_retrievers
    
    def get_thread_metadata(self, thread_id: str) -> dict:
        """Get metadata for a thread's document."""
        return self._thread_metadata.get(str(thread_id), {})
    
    def clear_thread_document(self, thread_id: str) -> None:
        """Remove document from a thread."""
        thread_id = str(thread_id)
        if thread_id in self._thread_retrievers:
            del self._thread_retrievers[thread_id]
        if thread_id in self._thread_metadata:
            del self._thread_metadata[thread_id]
    
    def get_all_threads_with_documents(self) -> list[str]:
        """Get list of thread IDs that have documents."""
        return list(self._thread_retrievers.keys())


# Create a global RAG manager instance
# This will be initialized in backend.py
rag_manager = None


def get_rag_manager() -> RAGManager:
    """Get the global RAG manager instance."""
    if rag_manager is None:
        raise ValueError("RAG manager not initialized. Call set_rag_manager() first.")
    return rag_manager


def set_rag_manager(manager: RAGManager):
    """Set the global RAG manager instance."""
    global rag_manager
    rag_manager = manager


@tool
def rag_tool(query: str, thread_id: str) -> dict:
    """
    Retrieve relevant information from the uploaded PDF for this chat thread.
    Always include the thread_id when calling this tool.
    """
    manager = get_rag_manager()
    retriever = manager._get_retriever(thread_id)
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }
    
    result = retriever.invoke(query)
    context = [doc.page_content for doc in result]
    metadata = [doc.metadata for doc in result]
    
    return {
        "query": query,
        "context": context,
        "metadata": metadata,
        "source_file": manager._thread_metadata.get(str(thread_id), {}).get("filename"),
    }