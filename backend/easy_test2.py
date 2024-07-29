import json
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

rooms = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, room_number: str, user_name: str, role: str):
        if room_number not in self.active_connections:
            self.active_connections[room_number] = []
        self.active_connections[room_number].append((user_name, websocket, role))
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, room_number: str, user_name: str):
        self.active_connections[room_number] = [
            (uname, ws, role) for uname, ws, role in self.active_connections[room_number] if ws != websocket
        ]
        if not self.active_connections[room_number]:
            del self.active_connections[room_number]

    async def broadcast(self, message: str, room_number: str, sender_name: str):
        for user_name, connection, role in self.active_connections.get(room_number, []):
            if user_name != sender_name:
                await connection.send_text(json.dumps({"sender": sender_name, "message": message}))

    async def send_private_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(json.dumps({"message": message}))


manager = ConnectionManager()


@app.websocket("/ws/create/{user_name}")
async def create_room(websocket: WebSocket, user_name: str):
    room_number = str(1234)  # str(random.randint(1000, 9999))
    rooms[room_number] = {
        "room_number": room_number,
        "status": 0,
        "join_members": [user_name],
        "time": 180,
        "creator": user_name,
    }

    await manager.connect(websocket, room_number, user_name, "creator")
    await websocket.send_text(json.dumps({"room_number": room_number}))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)

                if "command" in message_data:
                    if message_data["command"] == "update" and rooms[room_number]["creator"] == user_name:
                        rooms[room_number].update(message_data["data"])
                        await manager.send_private_message("Room settings updated", websocket)
                    elif message_data["command"] == "view":
                        await manager.send_private_message(json.dumps(rooms[room_number]), websocket)
                    else:
                        await manager.send_private_message("Unauthorized command or invalid permissions", websocket)
                else:
                    raise ValueError("Not a command")

            except ValueError:
                # Not a command, treat as a regular message
                print(f"Received data from {user_name} in room {room_number}: {data}")
                await manager.broadcast(data, room_number, user_name)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_number, user_name)
        print(f"Connection closed for user {user_name} in room {room_number}")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


@app.websocket("/ws/join/{room_number}/{user_name}")
async def join_room(websocket: WebSocket, room_number: str, user_name: str):
    if room_number not in rooms:
        await websocket.accept()
        await websocket.send_text(json.dumps({"error": "Room not found"}))
        await websocket.close()
        return

    rooms[room_number]["join_members"].append(user_name)
    await manager.connect(websocket, room_number, user_name, "joiner")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)

                if "command" in message_data:
                    if message_data["command"] == "view":
                        await manager.send_private_message(json.dumps(rooms[room_number]), websocket)
                    else:
                        await manager.send_private_message("Unauthorized command or invalid permissions", websocket)
                else:
                    raise ValueError("Not a command")

            except ValueError:
                # Not a command, treat as a regular message
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
