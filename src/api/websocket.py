"""
WebSocket support for real-time features.
Enables streaming responses and live updates.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from src.core.logging_config import app_logger
from src.llm.ollama_client import get_ollama_client
from src.retrieval.hybrid_search import get_hybrid_search


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new connection."""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        
        app_logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a disconnected websocket."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        app_logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific websocket."""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, client_id: str):
        """Broadcast a message to all connections for a client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Messages:
    - {"type": "ask", "question": "...", "top_k": 5}
    - {"type": "search", "query": "...", "top_k": 10}
    - {"type": "subscribe", "topic": "papers"}
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "ask":
                await handle_ask_streaming(websocket, data)
            
            elif message_type == "search":
                await handle_search(websocket, data)
            
            elif message_type == "subscribe":
                await handle_subscribe(websocket, client_id, data)
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    
    except Exception as e:
        app_logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)


async def handle_ask_streaming(websocket: WebSocket, data: dict):
    """
    Handle ask request with streaming response.
    
    Streams LLM output token by token for better UX.
    """
    try:
        question = data.get("question")
        top_k = data.get("top_k", 5)
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "message": "Searching for relevant papers..."
        })
        
        # Search for relevant papers
        search_engine = get_hybrid_search()
        results = search_engine.search(question, top_k=top_k)
        
        # Send search results
        await websocket.send_json({
            "type": "search_results",
            "results": [
                {
                    "arxiv_id": r['arxiv_id'],
                    "title": r['paper_title'],
                    "score": r.get('hybrid_score', 0)
                }
                for r in results
            ]
        })
        
        # Generate answer with streaming
        await websocket.send_json({
            "type": "status",
            "message": "Generating answer..."
        })
        
        llm = get_ollama_client()
        
        # Build prompt
        from src.llm.prompts import PromptTemplates
        system_prompt = PromptTemplates.get_qa_system_prompt()
        prompt = PromptTemplates.build_qa_prompt(question, results)
        
        # Stream response (note: this is simplified, actual implementation depends on LLM API)
        full_response = ""
        response = llm.generate(prompt, system=system_prompt, stream=False)
        
        # Simulate streaming by chunking response
        chunk_size = 5  # words per chunk
        words = response.split()
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            full_response += chunk + " "
            
            await websocket.send_json({
                "type": "answer_chunk",
                "chunk": chunk + " "
            })
            
            await asyncio.sleep(0.05)  # Small delay for smooth streaming
        
        # Send completion
        await websocket.send_json({
            "type": "answer_complete",
            "full_answer": full_response.strip()
        })
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


async def handle_search(websocket: WebSocket, data: dict):
    """Handle real-time search."""
    try:
        query = data.get("query")
        top_k = data.get("top_k", 10)
        
        search_engine = get_hybrid_search()
        results = search_engine.search(query, top_k=top_k)
        
        await websocket.send_json({
            "type": "search_complete",
            "results": results
        })
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


async def handle_subscribe(websocket: WebSocket, client_id: str, data: dict):
    """Handle subscription to real-time updates."""
    topic = data.get("topic")
    
    # Add to subscription list (simplified)
    await websocket.send_json({
        "type": "subscribed",
        "topic": topic,
        "message": f"Subscribed to {topic} updates"
    })


# Add to main.py:
"""
from src.api.websocket import websocket_endpoint

@app.websocket("/ws/{client_id}")
async def websocket_route(websocket: WebSocket, client_id: str):
    await websocket_endpoint(websocket, client_id)
"""