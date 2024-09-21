# %%
import asyncio
import json
from unittest.mock import AsyncMock

from constants import messages
from data_store import rooms
from fastapi import WebSocket
from helpers import current_time, ppprint
from templates import ROOM_TEMPLATE, USER_TEMPLATE


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

    def initialize_room(self, ROOM_CODE: str, USER_NAME: str, USER_ID: str):
        """新しいルームを初期化"""
        USER_ID = str(USER_ID)

        # ルーム情報を作成
        room = json.loads(json.dumps(ROOM_TEMPLATE))
        room["ROOM"]["ROOM_CODE"] = ROOM_CODE
        room["ROOM"]["ROOM_USER"][USER_ID] = {"USER_NUM": 1, "USER_NAME": USER_NAME}
        room["ROOM"]["ROOM_ROLE"].append(None)
        room["ROOM"]["ROOM_STATUS"] = "R002"
        room["ROOM"]["CREATED_AT"] = current_time()

        # ユーザ情報を作成
        user = json.loads(json.dumps(USER_TEMPLATE))
        user["USER_ID"] = USER_ID
        user["USER_NAME"] = USER_NAME
        user["USER_NUM"] = 1
        user["ROOM_CREATOR"] = True
        user["JOINED_AT"] = current_time()
        room["USERS"][USER_ID] = user
        room["USER"] = user

        # roomsにルームコードを登録
        rooms[ROOM_CODE] = room

    async def send_room_update(
        self,
        ROOM_CODE: int,
        STATUS_DETAIL_CODE: str = "S200",
        MESSAGE_CODE: str = "M000",
    ):
        """ルームの更新情報を全クライアントに送信"""

        print(current_time(), "send_room_update", ROOM_CODE, STATUS_DETAIL_CODE)
        if ROOM_CODE in self.active_connections:
            for USER_NAME, USER_ID, connection, _ in self.active_connections[ROOM_CODE]:
                data = rooms[ROOM_CODE]
                USER_ID = str(USER_ID)
                ROOM_STATUS = data["ROOM"]["ROOM_STATUS"]

                if ROOM_STATUS == "R004":  # 役職実行画面に各役職にメッセージ送信
                    role_id = rooms[ROOM_CODE]["USERS"][USER_ID].get("ROLE_ID")
                    MESSAGE_CODE = self.determine_message_code(role_id)

                # データ更新
                data.update(
                    {
                        "STATUS": {
                            "STATUS_CODE": "S200",
                            "STATUS_DETAIL_CODE": STATUS_DETAIL_CODE,
                            "MESSAGE_CODE": MESSAGE_CODE,
                            "MESSAGE_TEXT": messages.get(MESSAGE_CODE, "未知のメッセージコードです"),
                        },
                        "USER": rooms[ROOM_CODE]["USERS"][USER_ID],
                    }
                )

                try:
                    await connection.send_text(json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    print(current_time(), f"Error sending update to {USER_NAME}: {e}")

    def determine_message_code(self, role_id):
        """役職に応じたメッセージコードを決定"""
        if role_id == "20":
            return "M101"
        elif role_id == "21":
            return "M101"
        elif role_id == "22":
            return "M102"
        elif role_id == "23":
            return "M103"
        return "M000"

    async def send_error_message(
        self,
        websocket: WebSocket,
        status_code: str,
        status_detail_code: str = "S000",
        message_code: str = "M000",
        is_connected: bool = False,
    ):
        """エラーメッセージを送信"""

        if not is_connected:
            await websocket.accept()

        await websocket.send_text(
            json.dumps(
                {
                    "STATUS": {
                        "STATUS_CODE": status_code,
                        "STATUS_DETAIL_CODE": status_detail_code,
                        "MESSAGE_CODE": message_code,
                        "MESSAGE_TEXT": messages.get(message_code, "未定義のメッセージです"),
                    }
                },
                ensure_ascii=False,
            )
        )

        if not is_connected:
            await websocket.close()


async def _test():
    # ConnectionManager インスタンスを作成
    manager = ConnectionManager()

    # テスト用データ
    ROOM_CODE = "99999"
    USER_NAME = "fagi"
    USER_ID = "999"

    # モックされたWebSocketの作成
    mock_websocket = AsyncMock()

    # 接続情報をモックに追加
    manager.active_connections[ROOM_CODE] = [(USER_NAME, USER_ID, mock_websocket, "role")]

    # ルームの初期化
    manager.initialize_room(ROOM_CODE=ROOM_CODE, USER_NAME=USER_NAME, USER_ID=USER_ID)
    ppprint("initialize_room", json.dumps(rooms))

    # send_room_updateのテスト
    await manager.send_room_update("99999", "S201", "M011")
    # モックされたWebSocketにメッセージが送られたことを確認
    mock_websocket.send_text.assert_called_once()  # 1回だけ呼び出されたか確認
    ppprint("メッセージ送信成功:", mock_websocket.send_text.call_args[0][0])

    # send_error_messageのテスト
    await manager.send_error_message(mock_websocket, "S100", "S201", "M011", True)
    ppprint("メッセージ送信成功:", mock_websocket.send_text.call_args[0][0])

    await manager.send_error_message(mock_websocket, "S100", "S202", "M002", False)
    ppprint("メッセージ送信成功:", mock_websocket.send_text.call_args[0][0])


if __name__ == "__main__":
    await _test()  # type: ignore
