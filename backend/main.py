import random
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self.active_connections[room].remove(websocket)
        if len(self.active_connections[room]) == 0:
            del self.active_connections[room]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room: str):
        for connection in self.active_connections.get(room, []):
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{room}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room: str, client_id: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id}: {data}", room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast(f"{client_id} left the chat", room)


@app.get("/create_room")
async def create_room():
    room_number = str(random.randint(1000, 9999))
    return {"room_number": room_number}
    return {"room_number": room_number}
