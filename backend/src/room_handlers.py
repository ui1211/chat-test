import json
import random

from fastapi import APIRouter, FastAPI, Query, WebSocket, WebSocketDisconnect
from src.communication_handlers import CommunicationClass
from src.constants import DEBUG, debugs
from src.data_store import rooms
from src.helpers import current_time
from src.vote_handlers import voteManagerClass


class RoomManager:
    def __init__(self, manager):
        self.manager = manager  # ConnectionManager()
        self.communication = CommunicationClass(self.manager)
        self.voteManager = voteManagerClass(self.manager)

    async def handle_websocket_communication(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str, USER_ID: int):
        """WebSocket通信の処理"""
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if "MANAGE" in message_data:
                    pass
                    # await send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S200")
                elif "UPDATE" in message_data:
                    await self.communication.handle_update_command(websocket, message_data, ROOM_CODE, USER_ID)
                elif "EVENT" in message_data:
                    await self.communication.handle_event(websocket, message_data, ROOM_CODE, USER_NAME, USER_ID)
                elif "VOTE" in message_data:
                    await self.voteManager.handle_vote_command(message_data, ROOM_CODE, USER_ID)
                else:
                    print(current_time(), f"Received invalid data: {data}")

            except ValueError:
                print(current_time(), f"Error processing message from {USER_NAME} in room {ROOM_CODE}: {data}")

    async def handle_disconnect(self, ROOM_CODE: int, USER_NAME: str, USER_ID: int):
        """ユーザー切断処理 ルームの作成者が切断された場合、ルームと全ユーザーを削除"""
        # print(current_time(), "handle_disconnect", ROOM_CODE, USER_ID)
        try:
            # ユーザーの接続を削除
            await self.manager.disconnect(ROOM_CODE, USER_NAME)

            # USER_IDがrooms[ROOM_CODE]["USERS"]に存在するか確認
            if USER_ID in rooms[ROOM_CODE]["USERS"]:
                # room_createrの場合ルームを削除
                if rooms[ROOM_CODE]["USERS"][USER_ID].get("ROOM_CREATOR", False):
                    await self.manager.close_connections(ROOM_CODE)
                    del rooms[ROOM_CODE]
                    print(current_time(), f"delete room: room_code={ROOM_CODE}")
                else:
                    pass  # TODO
                    # # 切断されたユーザーがルーム内にいた場合、そのユーザーを削除
                    # if USER_ID in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]:
                    #     del rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][USER_ID]
                    #     rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].pop()

                    # # まだ他のユーザーが残っている場合は更新を送信
                    # if len(rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]) > 1:
                    #     await self.manager.send_room_update(ROOM_CODE)
            else:
                print(f"User {USER_ID} not found in room {ROOM_CODE}.")

            # print(f"Connection closed for user {USER_NAME} (ID: {USER_ID}) in room {ROOM_CODE}")
        except KeyError as e:
            print(current_time(), f"KeyError during disconnect: {e}")
        except Exception as e:
            print(current_time(), f"Error during disconnect: {e}")

    async def reassign_user_numbers(self, room_code: int):
        """USER_NUMを再度割り当てる（JOINED_ATでソートし詰めて付与）"""
        sorted_users = sorted(rooms[room_code]["USERS"].items(), key=lambda item: item[1]["JOINED_AT"])
        for index, (user_id, user_data) in enumerate(sorted_users):
            rooms[room_code]["USERS"][user_id]["USER_NUM"] = index + 1

    async def create_room(self, websocket: WebSocket, user_name: str):
        """ルーム作成とWebSocket接続の処理"""

        room_code = str(99999)  # str(random.randint(10000, 99999))
        user_id = str(999)  # str(random.randint(200, 999))

        print(current_time(), f"create_room: room_code={room_code}, user_name={user_name}")

        if not user_name:
            await self.manager.send_error_message(websocket, "S100", "S000", "M001")
            return

        self.manager.initialize_room(room_code, user_name, user_id)

        # webscoketの接続
        await self.manager.connect(websocket, room_code, user_name, user_id, "creator")
        await self.manager.send_room_update(room_code)

        try:
            await self.handle_websocket_communication(websocket, room_code, user_name, user_id)
        except WebSocketDisconnect:
            await self.handle_disconnect(room_code, user_name, user_id)
            await self.reassign_user_numbers(room_code)

    async def join_room(self, websocket: WebSocket, room_code: str, user_name: str):
        """ルーム参加とWebSocket接続の処理"""
        print(current_time(), f"join_room: room_code={room_code}, user_name={user_name}")

        if room_code == "" or user_name == "":
            await self.manager.send_error_message(websocket, "S100", "S000", "M002")
            return

        if room_code not in rooms:
            await self.manager.send_error_message(websocket, "S100", "S000", "M004")
            return

        if user_name in [user_data["USER_NAME"] for user_data in rooms[room_code]["ROOM"]["ROOM_USER"].values()]:
            print(current_time(), "join (but exists user name)", user_name)
            await self.manager.send_error_message(websocket, "S100", "S000", "M011")
            return

        # test
        if DEBUG:
            user_id = debugs["USER_ID"][user_name]
        else:
            # 重複しないユーザIDの取得
            room_users = set(rooms[room_code]["ROOM"]["ROOM_USER"].keys())
            available_ids = set(map(str, range(200, 1000)))
            user_id = random.choice(list(available_ids - room_users))

        user_num = len(rooms[room_code]["ROOM"]["ROOM_USER"]) + 1
        rooms[room_code]["ROOM"]["ROOM_USER"][user_id] = {
            "USER_NUM": user_num,
            "USER_NAME": user_name,
        }
        rooms[room_code]["ROOM"]["ROOM_ROLE"].append(None)
        user = self.manager.initialize_user(user_name, user_id, user_num)
        rooms[room_code]["USERS"][user_id] = user

        # webscoketの接続
        await self.manager.connect(websocket, room_code, user_name, user_id, "joiner")
        await self.manager.send_room_update(room_code)

        try:
            await self.handle_websocket_communication(websocket, room_code, user_name, user_id)
        except WebSocketDisconnect:
            await self.handle_disconnect(room_code, user_name, user_id)
            await self.reassign_user_numbers(room_code)
