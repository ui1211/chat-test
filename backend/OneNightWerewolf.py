import asyncio
import json
import random

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

##
from src.constants import codes, roles
from src.data_store import rooms
from src.manager import ConnectionManager
from src.template import ROOM_TEMPLATE, USER_TEMPLATE

app = FastAPI()
manager = ConnectionManager()


def initialize_room(ROOM_CODE: str, USER_NAME: str, USER_ID: str):
    """新しいルームを初期化"""
    USER_ID = str(USER_ID)

    # ルーム情報を作成
    room = json.loads(json.dumps(ROOM_TEMPLATE))
    room["ROOM"]["ROOM_CODE"] = ROOM_CODE
    room["ROOM"]["ROOM_USER"][USER_ID] = USER_NAME  # 不要
    room["ROOM"]["ROOM_ROLE"].append(None)
    room["ROOM"]["ROOM_STATUS"] = "R002"

    # ユーザ情報を作成
    user = json.loads(json.dumps(USER_TEMPLATE))
    user["USER_ID"] = USER_ID
    user["USER_NAME"] = USER_NAME
    user["ROOM_CREATOR"] = True
    room["USERS"][USER_ID] = user
    room["USER"] = user

    # roomsにルームコードを登録
    rooms[ROOM_CODE] = room


async def send_room_update(ROOM_CODE: int):
    """ルームの更新情報を全クライアントに送信"""
    if ROOM_CODE in manager.active_connections:
        for USER_NAME, USER_ID, connection, role in manager.active_connections[ROOM_CODE]:
            data = rooms[ROOM_CODE]
            USER_ID = str(USER_ID)

            data.update(
                {
                    "STATUS": {
                        "STATUS_CODE": "S200",
                        "MESSAGE_CODE": "M000",
                        "MESSAGE_TEXT": codes["M000"],
                    },
                    "USER": rooms[ROOM_CODE]["USERS"][USER_ID],
                }
            )
            await connection.send_text(json.dumps(data, ensure_ascii=False))


async def send_error_message(websocket: WebSocket, status_code: str, message_code: str, message_text: str):
    """エラーメッセージを送信"""

    await websocket.accept()
    await websocket.send_text(
        json.dumps(
            {
                "STATUS": {
                    "STATUS_CODE": status_code,
                    "MESSAGE_CODE": message_code,
                    "MESSAGE_TEXT": message_text,
                }
            },
            ensure_ascii=False,
        )
    )
    await websocket.close()


async def handle_event(message_data, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """イベントを処理"""
    event_type = message_data["EVENT"]

    if event_type == "OMAKASE_BUTTON":
        await process_omakase_button(USER_NAME, ROOM_CODE)
    elif event_type == "START_BUTTON":
        await process_start_button(USER_NAME, ROOM_CODE)
        await countdown_and_update(ROOM_CODE)
    elif event_type == "END_BUTTON":
        await process_end_button(USER_NAME, ROOM_CODE, USER_ID)
    else:
        print(f"Unknown event type: {event_type}")


async def countdown_and_update(ROOM_CODE: int):
    """カウントダウンを行い、ルーム状態を更新"""
    for i in range(10, 0, -1):
        print(f"Countdown: {i} seconds remaining...")
        await asyncio.sleep(1)
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R004"  # 役職実行画面に遷移
    await send_room_update(ROOM_CODE)


async def process_omakase_button(USER_NAME: str, ROOM_CODE: int):
    """おまかせボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    users_num = len(users) - 1

    if users_num == 3:
        role_list = [20, 21, 21, 22, 23]
    elif users_num == 4:
        role_list = [20, 20, 21, 21, 22, 23]
    elif users_num == 5:
        pass
    elif users_num == 6:
        pass

    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"] = role_list
    await send_room_update(ROOM_CODE)


async def process_start_button(USER_NAME: str, ROOM_CODE: int):
    """スタートボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

    # TODO　人数チェック(モック時は5人確定)

    valid_roles = [role for role in roles if role is not None]
    if len(valid_roles) < len(users):
        await manager.broadcast(
            json.dumps({"STATUS": {"STATU_CODE": "S400", "MESSAGE_CODE": "M005", "MESSAGE_TEXT": codes["M005"]}}),
            ROOM_CODE,
        )
        return

    assigned_roles = assign_roles_to_users(users, random.sample(roles, len(roles)))
    rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移

    await send_room_update(ROOM_CODE)


def assign_roles_to_users(users, roles):
    """ユーザーに役職を割り当て"""
    assigned_roles, i = {}, 0
    for user_id, user_name in users.items():
        if False:
            pass
            # TODO 後ほどバナナを実装
        else:
            role = roles[i]
            i += 1
        assigned_roles[str(user_id)] = {"USER_NAME": user_name, "USER_ROLE1": role, "USER_ROLE2": role}

    assigned_roles["100"] = {"USER_NAME": None, "USER_ROLE1": roles[i - 1], "USER_ROLE2": roles[i]}
    return assigned_roles


async def process_end_button(USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """エンドボタンの処理"""
    await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


async def handle_update_command(message_data, USER_NAME: str, ROOM_CODE: int):
    """更新コマンドの処理"""
    update_data = message_data.get("UPDATE")
    if update_data:
        if "ROLE" in update_data:
            await role_action_process(update_data["ROLE"], ROOM_CODE)
        else:
            selective_recursive_update(rooms[ROOM_CODE], update_data)
        await send_room_update(ROOM_CODE)
    else:
        await manager.broadcast(json.dumps({"STATUS": {"STATU_CODE": "E999"}}), ROOM_CODE)


async def role_action_process(role_data: dict, ROOM_CODE: int):
    if "FORTUNE_TELL" in role_data:
        user_id_to_fortune_tell = role_data["FORTUNE_TELL"]
        await execute_fortune_teller(ROOM_CODE, user_id_to_fortune_tell)
    elif "THIEF" in role_data:
        user_id_to_steal = role_data["THIEF"]
        await execute_thief(ROOM_CODE, user_id_to_steal)


async def execute_fortune_teller(ROOM_CODE: int, target_user_id: int):
    """占い師の行動を実行し、指定されたユーザーの役職を確認する"""
    room = rooms[ROOM_CODE]
    target_user_id = str(target_user_id)

    # 役職が確認されたユーザーが存在するかチェック
    if target_user_id in room["ROLE"]["ROLE_LIST"]:
        target_role = room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE1"]
        target_role_name = roles.get(str(target_role), "不明な役職")

        # 結果をルームに反映
        room["ROLE"]["FORTUNE_TELL"] = target_user_id
        # room["USER"]["VISIBLE_LIST"].append(target_user_id)
        # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} の役職は {target_role_name} です。"
        print(f"占い師はユーザーID {target_user_id} の役職 {target_role_name} を確認しました。")
    else:
        print(f"ユーザーID {target_user_id} はルームに存在しません。")
        # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} は存在しません。"

    await send_room_update(ROOM_CODE)


def execute_thief():
    # 怪盗処理
    pass


def selective_recursive_update(orig_dict, update_dict):
    """辞書を再帰的に更新"""
    for key, value in update_dict.items():
        if isinstance(value, dict) and isinstance(orig_dict.get(key), dict):
            selective_recursive_update(orig_dict[key], value)
        else:
            orig_dict[key] = value


async def handle_websocket_communication(websocket: WebSocket, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """WebSocket通信の処理"""
    while True:
        data = await websocket.receive_text()
        try:
            message_data = json.loads(data)
            if "UPDATE" in message_data:
                await handle_update_command(message_data, USER_NAME, ROOM_CODE)
            elif "EVENT" in message_data:
                await handle_event(message_data, USER_NAME, ROOM_CODE, USER_ID)
            else:
                print(f"Received invalid data: {data}")
        except ValueError:
            print(f"Error processing message from {USER_NAME} in room {ROOM_CODE}: {data}")


async def handle_disconnect(USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """ユーザー切断処理"""
    try:
        manager.disconnect(None, ROOM_CODE, USER_NAME)
        if rooms[ROOM_CODE]["USER"]["USER_ID"] == USER_ID:
            await manager.close_connections(ROOM_CODE)
            del rooms[ROOM_CODE]
        else:
            if USER_ID in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]:
                del rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][USER_ID]
                rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].pop()

            if len(rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]) > 1 or 100 not in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]:
                await send_room_update(ROOM_CODE)

        print(f"Connection closed for user {USER_NAME} (ID: {USER_ID}) in room {ROOM_CODE}")
    except Exception as e:
        print(f"Error during disconnect: {e}")


@app.get("/manage")
async def manage_room():
    """ルームの管理情報を出力"""
    print(f"room code : {rooms.keys()}")
    print(f"in room is {len(rooms)}")
    for ROOM_CODE in rooms.keys():
        print(ROOM_CODE, rooms[ROOM_CODE])


@app.websocket("/ws/create/")
async def create_room(websocket: WebSocket, USER_NAME: str = Query("")):
    """ルーム作成のWebSocketエンドポイント"""
    ROOM_CODE = str(99999)  # random.randint(10000, 99999)
    USER_ID = str(999)  # random.randint(200, 999)

    if not USER_NAME:
        await send_error_message(websocket, "S100", "M001", codes["M001"])
        return

    initialize_room(ROOM_CODE, USER_NAME, USER_ID)
    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "creator")
    await send_room_update(ROOM_CODE)

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


@app.websocket("/ws/join/")
async def join_room(websocket: WebSocket, ROOM_CODE: str = Query("0"), USER_NAME: str = Query("")):
    """ルーム参加のWebSocketエンドポイント"""

    if ROOM_CODE not in rooms:  # ルームコードが存在しない場合エラーを返す
        await send_error_message(websocket, "S100", "M004", codes["M004"])
        return

    if USER_NAME in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].values():  # ユーザ名が存在する場合エラーを返す
        await send_error_message(websocket, "S100", "M011", codes["M011"])
        return

    USER_ID = str(random.randint(200, 999))
    rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][USER_ID] = USER_NAME
    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].append(None)
    #
    user = json.loads(json.dumps(USER_TEMPLATE))
    user["USER_ID"] = USER_ID
    user["USER_NAME"] = USER_NAME
    rooms[ROOM_CODE]["USERS"][USER_ID] = user

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "joiner")
    await send_room_update(ROOM_CODE)

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)
