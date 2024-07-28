import json
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

rooms = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, room_number: str, user_name: str):
        if room_number not in self.active_connections:
            self.active_connections[room_number] = []
        self.active_connections[room_number].append((user_name, websocket))
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, room_number: str, user_name: str):
        self.active_connections[room_number] = [
            (uname, ws) for uname, ws in self.active_connections[room_number] if ws != websocket
        ]
        if not self.active_connections[room_number]:
            del self.active_connections[room_number]

    async def broadcast(self, message: str, room_number: str, sender_name: str):
        for user_name, connection in self.active_connections.get(room_number, []):
            if user_name != sender_name:
                await connection.send_text(json.dumps({"sender": sender_name, "message": message}))


manager = ConnectionManager()


@app.get("/create_room")
async def create_room(user_name: str):
    room_number = str(random.randint(1000, 9999))
    rooms[room_number] = [user_name]
    print(rooms)
    return {"room_number": room_number, "user_name": user_name}


@app.get("/check_room")
async def check_room(room_number: str):
    if room_number in rooms:
        return {"exists": True, "user_name": rooms[room_number]}
    else:
        return {"exists": False}


@app.get("/join_room")
async def join_room(room_number: str, user_name: str):
    if room_number in rooms:
        rooms[room_number].append(user_name)
        return {"exists": True, "user_name": rooms[room_number]}
    else:
        return {"exists": False}


@app.websocket("/ws/{room_number}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, room_number: str, user_name: str):
    await manager.connect(websocket, room_number, user_name)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data from {user_name} in room {room_number}: {data}")
            await manager.broadcast(data, room_number, user_name)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_number, user_name)
        print(f"Connection closed for user {user_name} in room {room_number}")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


@app.websocket("/ws_test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({"message": "WebSocket connection successful"}))
    await websocket.close()


# サーバーの起動
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
