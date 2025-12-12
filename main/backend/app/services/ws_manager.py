from typing import Dict, List, Tuple
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # {interview_id: [(websocket, role)]}
        self.active_connections: Dict[int, List[Tuple[WebSocket, str]]] = {}

    async def connect(self, interview_id: int, websocket: WebSocket, role: str):
        await websocket.accept()
        self.active_connections.setdefault(interview_id, []).append((websocket, role))

    def disconnect(self, interview_id: int, websocket: WebSocket):
        connections = self.active_connections.get(interview_id, [])
        self.active_connections[interview_id] = [
            (ws, r) for ws, r in connections if ws != websocket
        ]
        if not self.active_connections[interview_id]:
            self.active_connections.pop(interview_id, None)

    async def broadcast(self, interview_id: int, message: dict):
        connections = self.active_connections.get(interview_id, [])
        for ws, _ in connections:
            await ws.send_json(message)

    async def send_role(self, interview_id: int, message: dict, role: str):
        connections = self.active_connections.get(interview_id, [])
        for ws, r in connections:
            if r == role:
                await ws.send_json(message)


manager = ConnectionManager()
