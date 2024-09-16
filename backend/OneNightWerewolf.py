import asyncio
import json
import random
from datetime import datetime
from pprint import pprint

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

##
from src.constants import ALLOWED_COMMANDS, Countdown, codes, messages, roles_dict
from src.data_store import rooms
from src.manager import ConnectionManager
from src.templates import ROOM_TEMPLATE, USER_TEMPLATE

app = FastAPI()
manager = ConnectionManager()

print(str("====") * 10)
print(datetime.now())


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


async def send_room_update(ROOM_CODE: int, STATUS_CODE: str = "S200", MESSAGE_CODE: str = "M000"):
    print(datetime.now(), "send_room_update", ROOM_CODE, STATUS_CODE)
    """ルームの更新情報を全クライアントに送信"""
    if ROOM_CODE in manager.active_connections:
        print(datetime.now(), f"send in ROOM_CODE : {ROOM_CODE}")
        # pprint(manager.active_connections[ROOM_CODE])
        # print(len(manager.active_connections[ROOM_CODE]))

        index = 0
        for USER_NAME, USER_ID, connection, role in manager.active_connections[ROOM_CODE]:
            # print(datetime.now(), "test", index, USER_NAME, USER_ID, role)
            index += 1
            data = rooms[ROOM_CODE]
            USER_ID = str(USER_ID)
            ROOM_STATUS = data["ROOM"]["ROOM_STATUS"]

            # ルーム状態ごとの処理
            if ROOM_STATUS == "R001":  # スタート画面
                # 必要に応じて処理を追加
                pass

            elif ROOM_STATUS == "R002":  # ルーム作成/参加画面
                # 必要に応じて処理を追加
                pass

            elif ROOM_STATUS == "R003":  # 役職確認画面
                # 役職確認の処理
                pass

            elif ROOM_STATUS == "R004":  # 役職実行画面
                role_id = rooms[ROOM_CODE]["USERS"][USER_ID].get("ROLE_ID")

                if role_id == "20":  # 村人
                    MESSAGE_CODE = "M101"
                elif role_id == "21":  # 人狼
                    MESSAGE_CODE = "M101"
                elif role_id == "22":  # 占い師
                    MESSAGE_CODE = "M102"
                    # 例: 占い師の特殊処理をここで追加
                elif role_id == "23":  # 怪盗
                    MESSAGE_CODE = "M103"
                    # 例: 怪盗の特殊処理をここで追加

            elif ROOM_STATUS == "R005":  # 結果発表画面
                # 必要に応じて処理を追加
                pass

            else:
                # 不明な状態の場合はデフォルトメッセージコードを使用
                MESSAGE_CODE = "M000"

            # データ更新
            data.update(
                {
                    "STATUS": {
                        "STATUS_CODE": STATUS_CODE,
                        "MESSAGE_CODE": MESSAGE_CODE,
                        "MESSAGE_TEXT": messages.get(MESSAGE_CODE, "未知のメッセージコードです"),
                    },
                    "USER": rooms[ROOM_CODE]["USERS"][USER_ID],
                }
            )

            # 接続がまだ開いているか確認してからメッセージを送信
            try:
                print(datetime.now(), f"send in ROOM_CODE : {ROOM_CODE}, for USER_NAME: {USER_NAME}")
                # await asyncio.sleep(1)
                await connection.send_text(json.dumps(data, ensure_ascii=False))
            except Exception as e:
                # WebSocket送信でエラーが発生した場合、処理をスキップ
                print(f"Error sending update to {USER_NAME}: {e}")


async def send_error_message(websocket: WebSocket, status_code: str, message_code: str, is_connected: bool = False):
    """エラーメッセージを送信"""

    if not is_connected:
        await websocket.accept()

    await websocket.send_text(
        json.dumps(
            {
                "STATUS": {
                    "STATUS_CODE": status_code,
                    "MESSAGE_CODE": message_code,
                    "MESSAGE_TEXT": messages.get(message_code, "未定義のメッセージです"),
                }
            },
            ensure_ascii=False,
        )
    )

    if not is_connected:
        await websocket.close()


# ==========BUTTON==========


async def handle_event(websocket: WebSocket, message_data, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """イベントを処理"""
    event_type = message_data["EVENT"]

    if event_type == "OMAKASE_BUTTON":
        await process_omakase_button(ROOM_CODE)
    elif event_type == "START_BUTTON":
        await process_start_button(websocket, ROOM_CODE)
        await countdown_and_update(ROOM_CODE)  # 指定秒数待機後遷移
    elif event_type == "END_BUTTON":
        await process_end_button(USER_NAME, ROOM_CODE, USER_ID)
    else:
        print(f"Unknown event type: {event_type}")


async def countdown_and_update(ROOM_CODE: int):
    """カウントダウンを行い、ルーム状態を更新"""
    for i in range(Countdown, 0, -1):
        print(f"Countdown: {i} seconds remaining...")
        await asyncio.sleep(1)
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R004"  # 役職実行画面に遷移
    await send_room_update(ROOM_CODE, STATUS_CODE="S233")


async def process_omakase_button(ROOM_CODE: int):
    """おまかせボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    users_num = len(users) - 1

    if users_num == 3:
        role_list = [20, 21, 21, 22, 23]
    elif users_num == 4:
        role_list = [20, 20, 21, 21, 22, 23]
    elif users_num == 5:
        role_list = [20, 20, 20, 21, 21, 22, 23]
    elif users_num == 6:
        role_list = [20, 20, 20, 20, 21, 21, 22, 23]

    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"] = role_list
    await send_room_update(ROOM_CODE, STATUS_CODE="S231")


async def process_start_button(websocket: WebSocket, ROOM_CODE: int):
    """スタートボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

    # TODO　人数チェック(モック時は5人確定)

    valid_roles = [role for role in roles if role is not None]
    print(datetime.now(), "valid_roles", valid_roles)
    if len(valid_roles) < len(users):
        await send_error_message(websocket, "S400", "M005", is_connected=True)
        return

    roles = [str(i) for i in roles]  # 役職IDを文字列に変換

    assigned_roles = assign_roles_to_users(users, random.sample(roles, len(roles)))
    print(datetime.now(), "assigned_roles", assigned_roles)
    rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移

    # USERSのROLE_IDとROLE_NAMEを更新
    for user_id, role_data in assigned_roles.items():
        if user_id in rooms[ROOM_CODE]["USERS"]:
            rooms[ROOM_CODE]["USERS"][user_id]["ROLE_ID"] = role_data["USER_ROLE1"]
            rooms[ROOM_CODE]["USERS"][user_id]["ROLE_NAME"] = roles_dict[role_data["USER_ROLE1"]]

    # 役職ごとに異なるメッセージを送信
    ##TODO

    await send_room_update(ROOM_CODE, STATUS_CODE="S232")


# ==========ROLE==========


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


async def role_action_process(role_data: dict, ROOM_CODE: int):
    if "FORTUNE_TELL" in role_data:
        user_id_to_fortune_tell = role_data["FORTUNE_TELL"]
        await execute_fortune_teller(ROOM_CODE, user_id_to_fortune_tell)
    elif "THIEF" in role_data:
        user_id_to_steal = role_data["THIEF"]
        await execute_thief(ROOM_CODE, user_id_to_steal)


# 役職ごとの処理
## 占い師
async def execute_fortune_teller(ROOM_CODE: int, target_user_id: int):
    """占い師の行動を実行し、指定されたユーザーの役職を確認する"""
    room = rooms[ROOM_CODE]
    target_user_id = str(target_user_id)

    # 役職が確認されたユーザーが存在するかチェック
    if target_user_id in room["ROLE"]["ROLE_LIST"]:
        target_role = room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE1"]
        target_role_name = roles_dict.get(str(target_role), "不明な役職")

        # 結果をルームに反映
        room["ROLE"]["FORTUNE_TELL"] = target_user_id
        # room["USER"]["VISIBLE_LIST"].append(target_user_id)
        # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} の役職は {target_role_name} です。"
        print(f"占い師はユーザーID {target_user_id} の役職 {target_role_name} を確認しました。")
    else:
        print(f"ユーザーID {target_user_id} はルームに存在しません。")
        # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} は存在しません。"

    await send_room_update(ROOM_CODE)


## 怪盗
def execute_thief():
    # 怪盗処理
    pass


# ==========UPDATE==========


def selective_recursive_update(orig_dict, update_dict):
    """辞書を再帰的に更新し、変更があった場合 True とステータスコードを返す"""
    updated = False
    status_code = None

    for key, value in update_dict.items():
        if key in ALLOWED_COMMANDS:
            print(datetime.now(), "selective_recursive_update", key, value)
            if isinstance(value, dict) and isinstance(orig_dict.get(key), dict):
                # 再帰的にネストされた辞書も更新する
                recursive_update, recursive_status = selective_recursive_update(orig_dict[key], value)
                if recursive_update:
                    updated = True
                    status_code = recursive_status or status_code
            else:
                # 許可されたキーに基づき値を更新
                if orig_dict.get(key) != value:
                    orig_dict[key] = value
                    updated = True
                    status_code = ALLOWED_COMMANDS[key]  # 対応するステータスコードを設定
        else:
            print(datetime.now(), "Ignoring unallowed key:", key)

    return updated, status_code


async def handle_update_command(message_data, USER_NAME: str, ROOM_CODE: int):
    """更新コマンドの処理と通知"""
    update_data = message_data.get("UPDATE")
    print(datetime.now(), update_data)
    if update_data:
        if "ROLE" in update_data:
            await role_action_process(update_data["ROLE"], ROOM_CODE)
        else:
            # 許可されたキーを更新し、変更があった場合のみ send_room_update を発砲
            updated, status_code = selective_recursive_update(rooms[ROOM_CODE], update_data)
            if updated:
                # ステータスコードがある場合に send_room_update に渡す
                await send_room_update(ROOM_CODE, STATUS_CODE=status_code)
    else:
        await manager.broadcast(json.dumps({"STATUS": {"STATUS_CODE": "E999"}}), ROOM_CODE)


async def handle_websocket_communication(websocket: WebSocket, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """WebSocket通信の処理"""
    while True:
        data = await websocket.receive_text()
        try:
            message_data = json.loads(data)
            if "MANAGE" in message_data:
                await send_room_update(ROOM_CODE, STATUS_CODE="S200")
            elif "UPDATE" in message_data:
                await handle_update_command(message_data, USER_NAME, ROOM_CODE)
            elif "EVENT" in message_data:
                await handle_event(websocket, message_data, USER_NAME, ROOM_CODE, USER_ID)
            else:
                print(f"Received invalid data: {data}")

        except ValueError:
            print(f"Error processing message from {USER_NAME} in room {ROOM_CODE}: {data}")


async def handle_disconnect(USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """ユーザー切断処理"""
    try:
        manager.disconnect(ROOM_CODE, USER_NAME)
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


# ==========CONNECTION==========


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
        await send_error_message(websocket, "S100", "M001")
        return

    initialize_room(ROOM_CODE, USER_NAME, USER_ID)
    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "creator")
    await send_room_update(ROOM_CODE, STATUS_CODE="S200")

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


@app.websocket("/ws/join/")
async def join_room(websocket: WebSocket, ROOM_CODE: str = Query("0"), USER_NAME: str = Query("")):
    """ルーム参加のWebSocketエンドポイント"""

    print(datetime.now(), "join", ROOM_CODE, USER_NAME)

    if ROOM_CODE == "" or USER_NAME == "":
        await send_error_message(websocket, "S100", "M002")
        return

    if ROOM_CODE not in rooms:  # ルームコードが存在しない場合エラーを返す
        await send_error_message(websocket, "S100", "M004")
        return

    if USER_NAME in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].values():  # ユーザ名が存在する場合エラーを返す
        print(datetime.now(), "join (but exists user name)", USER_NAME)
        await send_error_message(websocket, "S100", "M011")
        return

    # ユーザIDの重複が内容生成
    room_users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].keys()
    while True:
        new_user_id = str(random.randint(200, 999))
        if new_user_id not in room_users:
            USER_ID = new_user_id
            break

    rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][USER_ID] = USER_NAME
    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].append(None)
    #
    user = json.loads(json.dumps(USER_TEMPLATE))
    user["USER_ID"] = USER_ID
    user["USER_NAME"] = USER_NAME
    rooms[ROOM_CODE]["USERS"][USER_ID] = user

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "joiner")
    await send_room_update(ROOM_CODE, STATUS_CODE="S200")

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


def generate_unique_user_id(room_users):
    """既存のユーザIDと重複しないIDを生成"""
    while True:
        new_user_id = str(random.randint(200, 999))
        if new_user_id not in room_users:
            return new_user_id
