from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_name: str):
        await websocket.accept()
        message = {"message": f"connect, {user_name}"}
        await websocket.send_json(message)

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()


manager = ConnectionManager()


@app.websocket("/ws/{user_name}")
async def websocket_endpoint(websocket: WebSocket, user_name: str):
    await manager.connect(websocket, user_name)

    try:
        while True:
            data = await websocket.receive_json()
            if "message" in data:
                text = data["message"]
                response = {"message": f"{text}, {user_name}"}
                await websocket.send_json(response)
                print(f"Sent message: {response} to {user_name}")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        print(f"Connection closed for user {user_name}")


# サーバーの起動
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
