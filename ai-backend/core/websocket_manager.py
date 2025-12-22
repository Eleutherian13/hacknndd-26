from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager for real-time communication"""
    
    def __init__(self):
        # Store active connections: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Store user subscriptions: {user_id: [client_ids]}
        self.user_subscriptions: Dict[str, List[str]] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Connect a new websocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Disconnect a websocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user subscriptions
        for user_id, clients in self.user_subscriptions.items():
            if client_id in clients:
                clients.remove(client_id)
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe_user(self, user_id: str, client_id: str):
        """Subscribe a client to user-specific updates"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = []
        
        if client_id not in self.user_subscriptions[user_id]:
            self.user_subscriptions[user_id].append(client_id)
            logger.info(f"Client {client_id} subscribed to user {user_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def send_to_user(self, message: dict, user_id: str):
        """Send message to all clients of a specific user"""
        if user_id in self.user_subscriptions:
            for client_id in self.user_subscriptions[user_id]:
                await self.send_personal_message(message, client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def notify_order_update(self, user_id: str, order_data: dict):
        """Notify user about order update"""
        message = {
            "type": "order_update",
            "data": order_data
        }
        await self.send_to_user(message, user_id)
    
    async def notify_prediction(self, user_id: str, prediction_data: dict):
        """Notify user about prediction/refill reminder"""
        message = {
            "type": "prediction",
            "data": prediction_data
        }
        await self.send_to_user(message, user_id)
    
    async def notify_agent_message(self, user_id: str, agent_type: str, message_text: str):
        """Send agent conversation message to user"""
        message = {
            "type": "agent_message",
            "agent": agent_type,
            "message": message_text
        }
        await self.send_to_user(message, user_id)


# Global connection manager instance
manager = ConnectionManager()
