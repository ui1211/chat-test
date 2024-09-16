# src/manager.py (修正後)
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, ROOM_CODE: str, USER_NAME: str, USER_ID: str, role: str):
        """新しいユーザーを接続し、接続リストに追加"""
        if ROOM_CODE not in self.active_connections:
            self.active_connections[ROOM_CODE] = []

        # 同じユーザーがすでに接続されていないかをチェック
        for connection in self.active_connections[ROOM_CODE]:
            if connection[1] == USER_ID:  # USER_IDが一致するか確認
                print(f"User {USER_NAME} with ID {USER_ID} is already connected. Skipping.")
                return  # 重複が発生している場合、追加しない

        self.active_connections[ROOM_CODE].append((USER_NAME, USER_ID, websocket, role))
        await websocket.accept()

    def disconnect(self, ROOM_CODE: str, USER_ID: str):
        """ユーザーを切断し、接続リストから削除"""
        if ROOM_CODE in self.active_connections:
            self.active_connections[ROOM_CODE] = [
                (uname, uid, ws, role) for uname, uid, ws, role in self.active_connections[ROOM_CODE] if uid != USER_ID
            ]
            if not self.active_connections[ROOM_CODE]:
                del self.active_connections[ROOM_CODE]

    async def broadcast(self, message: str, ROOM_CODE: str, sender_name: str = None):
        """メッセージを同じルーム内の全てのクライアントにブロードキャスト"""
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            if USER_NAME != sender_name:
                await connection.send_text(message)

    async def close_connections(self, ROOM_CODE: str):
        """全てのクライアントを切断"""
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            await connection.send_text(json.dumps({"STATUS": {"STATUS_CODE": "S201"}}))
            await connection.close()
        del self.active_connections[ROOM_CODE]
