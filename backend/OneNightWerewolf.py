import asyncio
import json
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

#  存在するすべての部屋を管理する変数
rooms = {}

# ルーム情報のテンプレート
ROOM_TEMPLATE = {
    "STATUS": {
        "STATUS_CODE": None,
        "MESSAGE_CODE": "",
        "MESSAGE_TEXT": "",
    },
    "ROOM": {
        "ROOM_CODE": None,
        "ROOM_NAME": "ワンナイト人狼",
        "ROOM_DISCUSSION_TIME": 180,
        "ROOM_STATUS": "R001",
        "ROOM_USER": [100],  # 墓場プレイヤー
        "ROOM_ROLE": [None, None],  # 初期配役
        "USER_LIST": {},
        "VOTED_USER_LIST": [],
    },
    "ROLE": {
        "FORTUNE_TELL": None,
        "THIEF": None,
        "ROLE_LIST": {},
    },
    "USER": {
        "USER_ID": None,
        "USER_NAME": None,
        "ROLE_ID": 10,
        "ROLE_NAME": None,
        "ROOM_CREATOR": True,
        "VISIBLE_LIST": [],
        "USER_VOTE": None,
    },
    "RESULT": {
        "RESULT_TEXT": "",
        "VOTE_RESULT": {},
    },
}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str, USER_ID: int, role: str):
        if ROOM_CODE not in self.active_connections:
            self.active_connections[ROOM_CODE] = []
        self.active_connections[ROOM_CODE].append((USER_NAME, USER_ID, websocket, role))
        await websocket.accept()
        await websocket.send_text(json.dumps({"STATUS": {"STATUS_CODE": 200}}))

    def disconnect(self, websocket: WebSocket, ROOM_CODE: int, USER_NAME: str):
        self.active_connections[ROOM_CODE] = [
            (uname, uid, ws, role) for uname, uid, ws, role in self.active_connections[ROOM_CODE] if ws != websocket
        ]
        if not self.active_connections[ROOM_CODE]:
            del self.active_connections[ROOM_CODE]

    async def broadcast(self, message: str, ROOM_CODE: int, sender_name: str = None):
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            if USER_NAME != sender_name:
                await connection.send_text(message)

    async def close_connections(self, ROOM_CODE: int):
        for USER_NAME, USER_ID, connection, role in self.active_connections.get(ROOM_CODE, []):
            await connection.send_text(json.dumps({"STATUS": {"STATUS_CODE": 201}}))
            await connection.close()


manager = ConnectionManager()


def initialize_room(ROOM_CODE: int, USER_NAME: str, USER_ID: int):
    room = json.loads(json.dumps(ROOM_TEMPLATE))  # 深いコピーを作成
    room["ROOM"]["ROOM_CODE"] = ROOM_CODE
    room["ROOM"]["ROOM_USER"].append(USER_ID)
    room["ROOM"]["ROOM_ROLE"].append(None)
    room["ROOM"]["USER_LIST"] = {USER_ID: USER_NAME}
    room["USER"]["USER_ID"] = USER_ID
    room["USER"]["USER_NAME"] = USER_NAME
    rooms[ROOM_CODE] = room


async def send_room_update(ROOM_CODE: int):
    if ROOM_CODE in manager.active_connections:
        for USER_NAME, USER_ID, connection, role in manager.active_connections[ROOM_CODE]:
            try:
                message = {
                    "STATUS": {"STATUS_CODE": 200, "MESSAGE_CODE": "M000", "MESSAGE_TEXT": "test"},
                    "ROOM": rooms[ROOM_CODE]["ROOM"],
                    "USER": {"USER_NAME": USER_NAME, "USER_ID": USER_ID, "ROOM_CREATOR": (role == "creator")},
                }
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except (RuntimeError, WebSocketDisconnect):
                print(f"Connection for {USER_NAME} in room {ROOM_CODE} is already closed or encountered an error.")


async def handle_event(message_data, USER_NAME: str, ROOM_CODE: int):
    event_type = message_data["EVENT"]

    if event_type == "OMAKASE_BUTTON":
        await process_omakase_button(USER_NAME, ROOM_CODE)
    elif event_type == "START_BUTTON":
        await process_start_button(USER_NAME, ROOM_CODE)
    elif event_type == "END_BUTTON":
        await process_end_button(USER_NAME, ROOM_CODE)
    else:
        print(f"Unknown event type: {event_type}")


async def process_omakase_button(USER_NAME: str, ROOM_CODE: int):
    # TODO お任せボタン押下時の処理をここに追加
    print(f"{USER_NAME} pressed OMAKASE_BUTTON in room {ROOM_CODE}")
    await send_room_update(ROOM_CODE)


async def process_start_button(USER_NAME: str, ROOM_CODE: int):
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

    if len(roles) < len(users):
        await manager.broadcast(
            json.dumps({"STATUS": {"STATU_CODE": "E001", "STATU_MESSAGE": "Insufficient roles"}}), ROOM_CODE
        )
        return

    roles = random.sample(roles, len(roles))

    assigned_roles = assign_roles_to_users(users, roles)

    rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移
    await send_room_update(ROOM_CODE)


def assign_roles_to_users(users, roles):
    assigned_roles, i = {}, 0
    for user_id in users:
        if user_id == 100:
            continue
        assigned_roles[user_id] = [roles[i], roles[i]]
        i += 1

    assigned_roles[100] = roles[-i:]  # 最後の残りの役職をID 100に割り当て
    return assigned_roles


async def process_end_button(USER_NAME: str, ROOM_CODE: int):
    # TODO ENDボタンの処理をここに追加
    print(f"{USER_NAME} pressed END_BUTTON in room {ROOM_CODE}")
    pass


def selective_recursive_update(orig_dict, update_dict):
    for key, value in update_dict.items():
        if key in orig_dict:
            if isinstance(value, dict) and isinstance(orig_dict[key], dict):
                selective_recursive_update(orig_dict[key], value)
            else:
                orig_dict[key] = value


async def handle_update_command(message_data, USER_NAME: str, ROOM_CODE: int):
    if rooms[ROOM_CODE]["USER"]["USER_NAME"] == USER_NAME:
        update_data = message_data.get("UPDATE")
        if update_data:
            selective_recursive_update(rooms[ROOM_CODE], update_data)
            await send_room_update(ROOM_CODE)
        else:
            await manager.broadcast(json.dumps({"STATUS": {"STATU_CODE": "E999"}}), ROOM_CODE)
    else:
        await manager.broadcast(json.dumps({"STATUS": {"STATU_CODE": "E999"}}), ROOM_CODE)


@app.websocket("/ws/create/{USER_NAME}")
async def create_room(websocket: WebSocket, USER_NAME: str):
    ROOM_CODE = 999999  # random.randint(100000, 999999)
    USER_ID = random.randint(200, 999)

    initialize_room(ROOM_CODE, USER_NAME, USER_ID)

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "creator")
    await send_room_update(ROOM_CODE)

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


@app.websocket("/ws/join/{ROOM_CODE}/{USER_NAME}")
async def join_room(websocket: WebSocket, ROOM_CODE: int, USER_NAME: str):
    if not validate_room_and_user(ROOM_CODE, USER_NAME, websocket):
        return

    USER_ID = random.randint(200, 999)
    rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].append(USER_ID)
    rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_ID] = USER_NAME
    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].append(None)

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "joiner")
    await send_room_update(ROOM_CODE)

    try:
        await handle_websocket_communication(websocket, USER_NAME, ROOM_CODE, USER_ID)
    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


def validate_room_and_user(ROOM_CODE: int, USER_NAME: str, websocket: WebSocket):
    if ROOM_CODE not in rooms:
        send_error_message_sync(websocket, 400, "M004", "ルームコードが間違っています")
        return False

    if USER_NAME in rooms[ROOM_CODE]["ROOM"]["USER_LIST"].values():
        send_error_message_sync(websocket, 400, "M000", "ユーザー名が重複")
        return False

    return True


def send_error_message_sync(websocket: WebSocket, status_code: int, message_code: str, message_text: str):
    asyncio.create_task(_send_error_message(websocket, status_code, message_code, message_text))


async def _send_error_message(websocket: WebSocket, status_code: int, message_code: str, message_text: str):
    await websocket.accept()
    await websocket.send_text(
        json.dumps(
            {
                "STATUS": {
                    "STATUS_CODE": status_code,
                    "MESSAGE_CODE": message_code,
                    "MESSAGET_TEXT": message_text,
                }
            }
        )
    )
    await websocket.close()


async def handle_websocket_communication(websocket: WebSocket, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """
    Handle the communication with a connected WebSocket user.
    """
    while True:
        data = await websocket.receive_text()
        try:
            message_data = json.loads(data)

            if "UPDATE" in message_data:
                await handle_update_command(message_data, USER_NAME, ROOM_CODE)
            elif "EVENT" in message_data:
                await handle_event(message_data, USER_NAME, ROOM_CODE)
            else:
                raise ValueError("Not a command")

        except ValueError:
            print(f"Received data from {USER_NAME} in room {ROOM_CODE}: {data}")
            await manager.broadcast(data, ROOM_CODE, USER_NAME)


async def handle_disconnect(USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """
    Handle user disconnection, remove the user from the room, and send updated room information.
    """
    # まず、ユーザーを接続リストから削除
    manager.disconnect(None, ROOM_CODE, USER_NAME)  # Disconnect the user from the connection manager

    if USER_ID in rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]:
        rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].remove(USER_ID)
    if USER_ID in rooms[ROOM_CODE]["ROOM"]["USER_LIST"]:
        del rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_ID]

    # ルームが空になった場合、ルームを削除
    if len(rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]) == 1 and rooms[ROOM_CODE]["ROOM"]["ROOM_USER"][0] == 100:
        del rooms[ROOM_CODE]
    else:
        # ここでルームの状態を他のクライアントに送信
        await send_room_update(ROOM_CODE)

    print(f"Connection closed for user {USER_NAME} (ID: {USER_ID}) in room {ROOM_CODE}")
