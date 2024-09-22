import asyncio
import json
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, FastAPI, Query, WebSocket, WebSocketDisconnect
from src.communication_handlers import CommunicationClass
from src.constants import DEBUG, debugs
from src.data_store import rooms
from src.helpers import current_time
from src.vote_handlers import voteManagerClass


class RoomManager:
    def __init__(self, manager):
        self.manager = manager
        self.communication = CommunicationClass(self.manager)
        self.voteManager = voteManagerClass(self.manager)

    async def handle_websocket_communication(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str, USER_ID: int):
        """WebSocket通信の処理"""
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                if "MANAGE" in message_data:
                    await self.manager.send_room_update(ROOM_CODE, "S290")
                elif "UPDATE" in message_data:
                    await self.communication.handle_update_command(websocket, message_data, ROOM_CODE, USER_ID)
                elif "EVENT" in message_data:
                    await self.communication.handle_event(websocket, message_data, ROOM_CODE, USER_NAME, USER_ID)
                elif "VOTE" in message_data:
                    await self.voteManager.handle_vote_command(message_data, ROOM_CODE, USER_ID)
                else:
                    pass
                    # 不正なコマンドを受信した場合
                    # print(current_time(), f"Received invalid data: {data}")

            except ValueError:
                print(current_time(), f"Error processing message from {USER_NAME} in room {ROOM_CODE}: {data}")

    # import asyncio
    # from datetime import datetime, timedelta

    async def countdown_and_update(
        self,
        websocket,
        room_code,
        user_name,
        user_id,
        room_status,
        countdown=5,
        loop_name="",
    ):
        """カウントダウンを行い、ルーム状態を更新しつつ、WebSocket通信を処理"""

        stop_event = asyncio.Event()

        async def countdown_timer(countdown_seconds):
            """現在時刻から指定秒数後に処理が終了するカウントダウン"""
            try:
                end_time = datetime.now() + timedelta(seconds=countdown_seconds)
                last_print_time = datetime.now()

                while not stop_event.is_set():
                    now = datetime.now()
                    remaining_time = (end_time - now).total_seconds()

                    # 1秒ごとに残り時間を表示
                    if (now - last_print_time).total_seconds() >= 1:
                        print(
                            current_time(),
                            f"{loop_name}: room_code={room_code}, Countdown: {int(remaining_time)}",
                        )
                        last_print_time = now

                    if remaining_time <= 0:
                        print(current_time(), f"{loop_name}: room_code={room_code} Countdown finished")
                        stop_event.set()  # カウントダウン終了を通知
                        break

                    # if rooms[room_code]["ROOM"]["ROOM_STATUS"] == room_status:
                    #     print(current_time(), f"countdown stop for {room_status}")
                    #     stop_event.set()
                    #     break

                    await asyncio.sleep(0.1)
            except Exception as e:
                print(current_time(), f"Error in countdown_timer: {e}")

        async def handle_websocket():
            """WebSocketでフロントエンドからのメッセージを受け付ける"""
            try:
                while not stop_event.is_set():
                    try:
                        await asyncio.wait_for(
                            self.handle_websocket_communication(websocket, room_code, user_name, user_id),
                            timeout=1,  # 1秒ごとにチェック
                        )
                        # await self.handle_websocket_communication(websocket, room_code, user_name, user_id)
                    except asyncio.TimeoutError:
                        continue  # タイムアウトでループを継続
                    except asyncio.CancelledError:
                        print(current_time(), "WebSocket task was cancelled.")
                        break
                    except Exception as e:
                        print(current_time(), f"WebSocket error: {e}")
                        break
            except Exception as e:
                print(current_time(), f"Error in handle_websocket: {e}")

        # カウントダウンとWebSocket通信を並行して実行
        try:
            await asyncio.gather(
                countdown_timer(countdown),
                handle_websocket(),
            )
        except Exception as e:
            print(current_time(), f"Error in countdown_and_update: {e}")

        # カウントダウンとWebSocketの処理が終了したら、次の処理に戻る
        print(current_time(), f"{loop_name}: room_code={room_code}, 終了")
        return True

    async def handle_disconnect(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str, USER_ID: int):
        """ユーザー切断処理 ルームの作成者が切断された場合、ルームと全ユーザーを削除"""
        print(current_time(), f"切断処理: room_code={ROOM_CODE}, user_name={USER_NAME}")
        try:
            # ユーザーの接続を削除
            await self.manager.disconnect(ROOM_CODE, USER_ID, USER_NAME)

            # USER_IDがrooms[ROOM_CODE]["USERS"]に存在するか確認
            if USER_ID in rooms[ROOM_CODE]["USERS"]:
                # createrの場合ルームを削除しルーム参加者のコネクションを切断
                if rooms[ROOM_CODE]["USERS"][USER_ID].get("ROOM_CREATOR", False):
                    # ルームが削除されたことを送信
                    # if len(rooms[ROOM_CODE]["USERS"]) >= 1:
                    #     await self.manager.send_room_update(ROOM_CODE, "S291")

                    await self.manager.close_connections(ROOM_CODE)
                    del rooms[ROOM_CODE]
                    print(current_time(), f"delete room: room_code={ROOM_CODE}")
                # joinerの場合、ユーザデータを削除
                else:
                    if USER_ID in rooms[ROOM_CODE]["USERS"].keys():
                        rooms[ROOM_CODE]["USERS"].pop(USER_ID)

            else:
                print(f"User {USER_ID} not found in room {ROOM_CODE}.")

            # print(f"Connection closed for user {USER_NAME} (ID: {USER_ID}) in room {ROOM_CODE}")
        except KeyError as e:
            print(current_time(), f"KeyError during disconnect: {e}")
        except Exception as e:
            print(current_time(), f"Error during disconnect: {e}")

        # user_numを再振り分けと送信
        if ROOM_CODE in rooms.keys():
            await self.reassign_user_numbers(ROOM_CODE)
            # まだ他のユーザーが残っている場合は更新を送信
            if len(rooms[ROOM_CODE]["USERS"]) >= 1:
                await self.manager.send_room_update(ROOM_CODE, "S291")

    async def reassign_user_numbers(self, room_code: int):
        """USER_NUMを再度割り当てる（JOINED_ATでソートし詰めて付与）"""
        sorted_users = sorted(rooms[room_code]["USERS"].items(), key=lambda item: item[1]["JOINED_AT"])
        for index, (user_id, user_data) in enumerate(sorted_users):
            rooms[room_code]["USERS"][user_id]["USER_NUM"] = index + 1

        room_user = {}
        for user_id, user_data in rooms[room_code]["USERS"].items():
            room_user[user_id] = {
                "USER_NUM": user_data["USER_NUM"],
                "USER_NAME": user_data["USER_NAME"],
            }
        rooms[room_code]["ROOM"]["ROOM_USER"] = room_user

    def generate_unique_id(self, existing_ids, id_range=(200, 999)):
        """既存のIDリストに含まれないランダムなIDを生成"""
        # 既存のIDをセットに変換して高速検索ができるようにする
        existing_ids = set(existing_ids)
        # 指定された範囲内のIDの集合を作成
        available_ids = set(map(str, range(id_range[0], id_range[1] + 1)))
        # 既存のIDを除外した中からランダムに1つ選択
        unique_id = str(random.choice(list(available_ids - existing_ids)))

        return unique_id

    async def create_room(self, websocket: WebSocket, user_name: str):
        """ルーム作成とWebSocket接続の処理"""

        if DEBUG:
            room_code = str(99999)  # str(random.randint(10000, 99999))
            user_id = str(999)  # str(random.randint(200, 999))
        else:
            room_code = str(self.generate_unique_id(list(rooms.keys()), (10000, 99999)))
            user_id = str(random.randint(200, 999))

        print(current_time(), f"create_room: room_code={room_code}, user_name={user_name}")

        if user_name == "":
            await self.manager.send_error_message(websocket, "S100", "S121", "M001")
            return

        self.manager.initialize_room(room_code, user_name, user_id)

        # webscoketの接続
        await self.manager.connect(websocket, room_code, user_name, user_id, "creator")
        await self.manager.send_room_update(room_code, "S221")

        try:
            await self.handle_websocket_communication(websocket, room_code, user_name, user_id)
        except WebSocketDisconnect:
            await self.handle_disconnect(websocket, room_code, user_name, user_id)
            # await self.reassign_user_numbers(room_code)

    async def join_room(self, websocket: WebSocket, room_code: str, user_name: str):
        """ルーム参加とWebSocket接続の処理"""
        print(current_time(), f"join_room: room_code={room_code}, user_name={user_name}")

        if room_code == "" or user_name == "":
            await self.manager.send_error_message(websocket, "S100", "S122", "M002")
            return

        if room_code not in rooms:
            await self.manager.send_error_message(websocket, "S100", "S124", "M004")
            return

        if user_name in [user_data["USER_NAME"] for user_data in rooms[room_code]["ROOM"]["ROOM_USER"].values()]:
            print(current_time(), "join (but exists user name)", user_name)
            await self.manager.send_error_message(websocket, "S100", "S125", "M011")
            return

        # test
        if DEBUG:
            user_id = debugs["USER_ID"][user_name]
        else:
            user_id = self.generate_unique_id(rooms[room_code]["ROOM"]["ROOM_USER"].keys(), (200, 999))
            # room_users = set(rooms[room_code]["ROOM"]["ROOM_USER"].keys())
            # available_ids = set(map(str, range(200, 1000)))
            # user_id = random.choice(list(available_ids - room_users))

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
        await self.manager.send_room_update(room_code, "S222")

        try:
            await self.handle_websocket_communication(websocket, room_code, user_name, user_id)
        except WebSocketDisconnect:
            await self.handle_disconnect(websocket, room_code, user_name, user_id)
            # await self.reassign_user_numbers(room_code)
