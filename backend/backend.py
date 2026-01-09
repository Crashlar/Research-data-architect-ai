from __future__ import annotations

import sqlite3
from typing import Annotated,  Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# Import RAG module - IMPORTANT: import the rag_tool directly
from backend.my_tools.rag import rag_tool, RAGManager, set_rag_manager

load_dotenv()

# -------------------
# 1. LLM + embeddings + RAG Manager
# -------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

# Initialize RAG manager and set it globally
rag_manager = RAGManager(embeddings=embeddings)
set_rag_manager(rag_manager)

# -------------------
# 2. Tools - import all 
# -------------------
from backend.my_tools.builtintools import duckduckgo_search , wikipedia_search
from backend.my_tools.custom_tools import calculator , get_stock_price
from backend.my_tools.databasetool import sql_to_text_output
from backend.my_tools.rag import rag_tool


# all tool including rag tool 
tools = [duckduckgo_search,wikipedia_search , sql_to_text_output, get_stock_price, calculator, rag_tool]
llm_with_tools = llm.bind_tools(tools)

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState, config=None):
    """LLM node that may answer or request a tool call."""
    thread_id = None
    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    system_message = SystemMessage(
        content=(
            "You are a helpful assistant. For questions about the uploaded PDF, call "
            "the `rag_tool` and include the thread_id "
            f"`{thread_id}`. You can also use the web search, stock price, and "
            "calculator tools when helpful. If no document is available, ask the user "
            "to upload a PDF."
        )
    )

    messages = [system_message, *state["messages"]]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}


tool_node = ToolNode(tools)

# -------------------
# 5. Checkpointer
# -------------------
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# -------------------
# 6. Graph
# -------------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

# -------------------
# 7. Helper functions - proxy to rag_manager
# -------------------
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
    Proxy function to RAG manager's ingest_pdf.
    
    Args:
        file_bytes: PDF file bytes
        thread_id: Unique identifier for the chat thread
        filename: Original filename (optional)
        
    Returns:
        dict: Summary information about the ingested document
    """
    return rag_manager.ingest_pdf(file_bytes, thread_id, filename)


def thread_has_document(thread_id: str) -> bool:
    """Proxy function to RAG manager."""
    return rag_manager.thread_has_document(thread_id)


def thread_document_metadata(thread_id: str) -> dict:
    """Proxy function to RAG manager."""
    return rag_manager.get_thread_metadata(thread_id)


def clear_thread_document(thread_id: str) -> None:
    """Proxy function to RAG manager."""
    return rag_manager.clear_thread_document(thread_id)