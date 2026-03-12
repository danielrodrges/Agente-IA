"""
WebSocket Manager para notificações em tempo real do painel do atendente.
"""
import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Gerencia conexões WebSocket para o painel do atendente."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Aceita e registra nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket conectado. Total conexões: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove conexão WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket desconectado. Total conexões: {len(self.active_connections)}")

    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        """Envia mensagem para uma conexão específica."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Envia mensagem para todas as conexões ativas."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Conexão WebSocket fechada: {e}")
                disconnected.append(connection)
        
        # Limpar conexões mortas
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Retorna número de conexões ativas."""
        return len(self.active_connections)


# Singleton global
manager = WebSocketManager()
