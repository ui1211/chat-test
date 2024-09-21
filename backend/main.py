import random

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from src.data_store import rooms
from src.helpers import current_time
from src.manager import ConnectionManager


class RoomManager:
    def __init__(self):
        self.manager = ConnectionManager()

    async def handle_websocket_communication(self, websocket: WebSocket, user_name: str, room_code: str, user_id: str):
        """WebSocketのメイン処理"""
        # TODO UPDATE, EVENTなどの処理のこと
        while True:
            data = await websocket.receive_text()
            # ここでメッセージの処理を行う
            print(f"Received data from {user_name}: {data}")
            await websocket.send_text(f"Message received: {data}")

    # async def handle_disconnect(self, user_name: str, room_code: str, user_id: str):
    #     """切断時の処理"""
    #     print(f"{user_name} disconnected from room {room_code}.")
    #     self.manager.disconnect(room_code, user_id)

    async def handle_disconnect(self, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
        """ユーザー切断処理 ルームの作成者が切断された場合、ルームと全ユーザーを削除"""
        print(current_time(), "handle_disconnect", ROOM_CODE, USER_ID)
        try:
            # ユーザーの接続を削除
            await self.manager.disconnect(ROOM_CODE, USER_NAME)

            # USER_IDがrooms[ROOM_CODE]["USERS"]に存在するか確認
            if USER_ID in rooms[ROOM_CODE]["USERS"]:
                # ルームに作成者がいて、そのユーザーIDが切断された場合
                if rooms[ROOM_CODE]["USERS"][USER_ID].get("ROOM_CREATOR", False):
                    # ルームのすべての接続を閉じ、ルームを削除
                    await self.manager.close_connections(ROOM_CODE)
                    del rooms[ROOM_CODE]
                    print(f"Room {ROOM_CODE} has been deleted because the creator {USER_NAME} disconnected.")
                else:
                    # 切断されたユーザーがルーム内にいた場合、そのユーザーを削除
                    if USER_ID in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]:
                        del rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][USER_ID]
                        rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].pop()

                    # まだ他のユーザーが残っている場合は更新を送信
                    if len(rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]) > 1:
                        await self.manager.send_room_update(ROOM_CODE)
            else:
                print(f"User {USER_ID} not found in room {ROOM_CODE}.")

            print(f"Connection closed for user {USER_NAME} (ID: {USER_ID}) in room {ROOM_CODE}")
        except KeyError as e:
            # ルームコードやユーザーIDに関連するKeyErrorの処理
            print(current_time(), f"KeyError during disconnect: {e}")
        except Exception as e:
            # その他のエラー処理
            print(current_time(), f"Error during disconnect: {e}")

    async def reassign_user_numbers(room_code: int):
        """USER_NUMを再度割り当てる（JOINED_ATでソートし詰めて付与）"""
        # ユーザーをJOINED_ATでソート
        sorted_users = sorted(rooms[room_code]["USERS"].items(), key=lambda item: item[1]["JOINED_AT"])

        # USER_NUMを再割り当て
        for index, (user_id, user_data) in enumerate(sorted_users):
            rooms[room_code]["USERS"][user_id]["USER_NUM"] = index + 1  # 1から順番に付与
        print(f"Reassigned USER_NUMs in room {room_code}")

    async def create_room(self, websocket: WebSocket, user_name: str):
        """ルーム作成とWebSocket接続の処理"""
        room_code = str(random.randint(10000, 99999))
        user_id = str(random.randint(200, 999))

        if not user_name:
            await self.manager.send_error_message(websocket, "S100", "S101", "M001")
            return

        # ルーム初期化
        self.manager.initialize_room(room_code, user_name, user_id)

        # WebSocket接続
        await self.manager.connect(websocket, room_code, user_name, user_id, "creator")

        # ルームの更新情報を送信
        await self.manager.send_room_update(room_code)

        # WebSocketの通信処理
        try:
            await self.handle_websocket_communication(websocket, user_name, room_code, user_id)
        except WebSocketDisconnect:
            await self.handle_disconnect(user_name, room_code, user_id)
            await self.reassign_user_numbers(room_code)


# FastAPI用のエンドポイントを定義
router = APIRouter()
room_manager = RoomManager()


@router.websocket("/ws/create/")
async def websocket_create_room(websocket: WebSocket, user_name: str = Query("")):
    """WebSocketでルームを作成"""
    await room_manager.create_room(websocket, user_name)
