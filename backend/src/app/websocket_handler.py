"""
WebSocket Handler for Real-time Updates

Provides WebSocket endpoints for:
- Real-time indexing progress
- Live search results
- Agent execution streaming
- Conversation updates
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        """
        Accept WebSocket connection and add to channel.
        
        Args:
            websocket: WebSocket connection
            channel: Channel name (e.g., 'indexing', 'chat', 'search')
        """
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        logger.info(f"Client connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """
        Remove WebSocket connection from channel.
        
        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"Client disconnected from channel: {channel}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, channel: str):
        """
        Broadcast message to all clients in channel.
        
        Args:
            message: Message data
            channel: Channel name
        """
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections[channel].discard(conn)


# Global connection manager
manager = ConnectionManager()


async def websocket_indexing_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for indexing progress.
    
    Streams real-time updates about indexing progress.
    """
    await manager.connect(websocket, f"indexing:{session_id}")
    
    try:
        while True:
            # This would be called by the indexing pipeline
            # For now, simulate progress updates
            data = await websocket.receive_text()
            
            # Echo back (in production, this would be server-driven)
            await manager.send_personal_message({
                "type": "indexing_progress",
                "session_id": session_id,
                "data": json.loads(data)
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"indexing:{session_id}")
        logger.info(f"Indexing WebSocket closed for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, f"indexing:{session_id}")


async def websocket_chat_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for chat streaming.
    
    Streams LLM responses token-by-token.
    """
    await manager.connect(websocket, f"chat:{session_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message and stream response
            if data.get("type") == "chat_message":
                # This would call LLM client with streaming
                # For now, simulate streaming response
                message = data.get("message", "")
                
                # Simulate token streaming
                response_tokens = f"Response to: {message}".split()
                
                for token in response_tokens:
                    await manager.send_personal_message({
                        "type": "chat_token",
                        "session_id": session_id,
                        "token": token + " ",
                    }, websocket)
                    
                    await asyncio.sleep(0.05)  # Simulate delay
                
                # Send completion
                await manager.send_personal_message({
                    "type": "chat_complete",
                    "session_id": session_id,
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"chat:{session_id}")
        logger.info(f"Chat WebSocket closed for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, f"chat:{session_id}")


async def websocket_agent_execution(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for agent execution updates.
    
    Streams agent execution progress and intermediate results.
    """
    await manager.connect(websocket, f"agent:{task_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "start_task":
                # This would trigger agent orchestration
                # Stream updates as agents work
                
                # Simulate agent execution steps
                steps = [
                    "Parsing query...",
                    "Retrieving relevant code...",
                    "Analyzing context...",
                    "Generating response...",
                    "Complete!"
                ]
                
                for idx, step in enumerate(steps):
                    await manager.send_personal_message({
                        "type": "agent_progress",
                        "task_id": task_id,
                        "step": idx + 1,
                        "total_steps": len(steps),
                        "message": step,
                        "progress": (idx + 1) / len(steps),
                    }, websocket)
                    
                    await asyncio.sleep(0.5)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"agent:{task_id}")
        logger.info(f"Agent WebSocket closed for task: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, f"agent:{task_id}")


# Helper function to broadcast indexing updates
async def broadcast_indexing_update(session_id: str, update_data: dict):
    """
    Broadcast indexing update to all listeners.
    
    Called by indexing pipeline to push updates.
    """
    await manager.broadcast({
        "type": "indexing_update",
        "session_id": session_id,
        "data": update_data,
    }, f"indexing:{session_id}")


# Helper function to broadcast chat tokens
async def broadcast_chat_token(session_id: str, token: str):
    """
    Broadcast chat token to session.
    
    Called by LLM client during streaming.
    """
    await manager.broadcast({
        "type": "chat_token",
        "session_id": session_id,
        "token": token,
    }, f"chat:{session_id}")
