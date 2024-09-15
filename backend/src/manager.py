import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str, USER_ID: int, role: str):
        """新しいユーザーを接続し、接続リストに追加"""
        if ROOM_CODE not in self.active_connections:
            self.active_connections[ROOM_CODE] = []
        self.active_connections[ROOM_CODE].append((USER_NAME, USER_ID, websocket, role))
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str):
        """ユーザーを切断し、接続リストから削除"""
        self.active_connections[ROOM_CODE] = [
            (uname, uid, ws, role) for uname, uid, ws, role in self.active_connections[ROOM_CODE] if ws != websocket
        ]
        if not self.active_connections[ROOM_CODE]:
            del self.active_connections[ROOM_CODE]

    async def broadcast(self, message: str, ROOM_CODE: int, sender_name: str = None):
        """メッセージを同じルーム内の全てのクライアントにブロードキャスト"""
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            if USER_NAME != sender_name:
                await connection.send_text(message)

    async def close_connections(self, ROOM_CODE: int):
        """全てのクライアントを切断"""
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            await connection.send_text(json.dumps({"STATUS": {"STATUS_CODE": "S201"}}))
            await connection.close()
