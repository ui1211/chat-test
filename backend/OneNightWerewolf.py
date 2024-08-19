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
        "ROOME_CREATOR": True,
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
            (uname, ws, role) for uname, ws, role in self.active_connections[ROOM_CODE] if ws != websocket
        ]
        if not self.active_connections[ROOM_CODE]:
            del self.active_connections[ROOM_CODE]

    async def broadcast(self, message: str, ROOM_CODE: int, sender_name: str = None):
        for USER_NAME, connection, role in self.active_connections.get(ROOM_CODE, []):
            if USER_NAME != sender_name:
                await connection.send_text(message)

    async def close_connections(self, ROOM_CODE: int):
        for USER_NAME, connection, role in self.active_connections.get(ROOM_CODE, []):
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
    for USER_NAME, USER_ID, connection, role in manager.active_connections.get(ROOM_CODE, []):
        message = {
            "STATUS": {"STATUS_CODE": 200, "MESSAGE_CODE": "M000", "MESSAGE_TEXT": "test"},
            "ROOM": rooms[ROOM_CODE]["ROOM"],
            "USER": {"USER_NAME": USER_NAME, "USER_ID": USER_ID, "ROOM_CREATOR": (role == "creator")},
        }
        await connection.send_text(json.dumps(message, ensure_ascii=False))


async def handle_event(message_data, USER_NAME: str, ROOM_CODE: int):
    if "OMAKASE_BUTTON" in message_data["EVENT"]:
        # TODO お任せボタン押下時の処理をここに追加
        print(f"{USER_NAME} pressed OMAKASE_BUTTON in room {ROOM_CODE}")
        await send_room_update(ROOM_CODE)

    elif "START_BUTTON" in message_data["EVENT"]:
        print(rooms[ROOM_CODE])
        users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
        roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]
        print(users, roles)

        # 役職の数とユーザー数が一致するか確認
        if len(roles) < len(users):
            # エラー処理: 役職が不足している
            await manager.broadcast(
                json.dumps({"STATUS": {"STATU_CODE": "E001", "STATU_MESSAGE": "Insufficient roles"}}), ROOM_CODE
            )
            return

        roles = random.sample(roles, len(roles))
        print("Shuffled roles:", roles)

        assigned_roles, i = {}, 0
        for user_id in users:
            if user_id == 100:
                continue
            assigned_roles[user_id] = [roles[i], roles[i]]
            i += 1

        assigned_roles[100] = roles[-i:]  # 最後の残りの役職をID 100に割り当て
        print("Assigned roles:", assigned_roles)

        rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移
        await send_room_update(ROOM_CODE)

    elif "END_BUTTON" in message_data["EVENT"]:
        # TODO ENDボタンの処理をここに追加
        print(f"{USER_NAME} pressed END_BUTTON in room {ROOM_CODE}")
        pass


def selective_recursive_update(orig_dict, update_dict):
    for key, value in update_dict.items():
        if key in orig_dict:  # キーが存在する場合のみ処理を進める
            if isinstance(value, dict) and isinstance(orig_dict[key], dict):
                selective_recursive_update(orig_dict[key], value)  # 再帰的に更新
            else:
                orig_dict[key] = value  # 既存のキーの場合、値を更新


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
    ROOM_CODE = 999999  # random.randint(100000, 999999)  # TODO 重複チェック
    USER_ID = random.randint(200, 999)  # TODO 重複チェック

    initialize_room(ROOM_CODE, USER_NAME, USER_ID)

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "creator")
    await send_room_update(ROOM_CODE)

    try:
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

    except WebSocketDisconnect:
        await handle_disconnect(USER_NAME, ROOM_CODE)


@app.websocket("/ws/join/{ROOM_CODE}/{USER_NAME}")
async def join_room(websocket: WebSocket, ROOM_CODE: int, USER_NAME: str):
    if ROOM_CODE not in rooms:
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "STATUS": {
                        "STATUS_CODE": 400,
                        "MESSAGE_CODE": "M004",
                        "MESSAGET_TEXT": "ルームコードが間違っています",
                    }
                }
            )
        )
        await websocket.close()
        return

    if USER_NAME in rooms[ROOM_CODE]["ROOM"]["USER_LIST"].values():
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "STATUS": {
                        "STATUS_CODE": 400,
                        "MESSAGE_CODE": "M000",
                        "MESSAGET_TEXT": "ユーザー名が重複",
                    }
                }
            )
        )
        await websocket.close()
        return

    USER_ID = random.randint(200, 999)
    rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].append(USER_ID)
    rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_ID] = USER_NAME
    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"].append(None)

    await manager.connect(websocket, ROOM_CODE, USER_NAME, USER_ID, "joiner")
    await send_room_update(ROOM_CODE)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)

                if "EVENT" in message_data and "EXIT_BUTTON" in message_data["EVENT"]:
                    rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].remove(USER_ID)
                    del rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_ID]
                    await websocket.send_text(
                        json.dumps({"STATUS": {"STATU_CODE": "S001", "STATU_MESSAGE": "User exited"}})
                    )
                    await websocket.close()
                    await send_room_update(ROOM_CODE)

            except ValueError:
                print(f"Received data from {USER_NAME} in room {ROOM_CODE}: {data}")
                await manager.broadcast(data, ROOM_CODE, USER_NAME)

    except WebSocketDisconnect:
        manager.disconnect(websocket, ROOM_CODE, USER_NAME)
        rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].remove(USER_ID)
        del rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_ID]
        await send_room_update(ROOM_CODE)
        print(f"Connection closed for user {USER_NAME} in room {ROOM_CODE}")


async def handle_disconnect(USER_NAME: str, ROOM_CODE: int):
    if rooms[ROOM_CODE]["USER"]["USER_NAME"] == USER_NAME:
        await manager.broadcast(json.dumps({"STATUS": "disconnect"}), ROOM_CODE)
        await manager.close_connections(ROOM_CODE)
        del rooms[ROOM_CODE]
    else:
        manager.disconnect(websocket, ROOM_CODE, USER_NAME)
        rooms[ROOM_CODE]["ROOM"]["ROOM_USER"].remove(USER_NAME)
        del rooms[ROOM_CODE]["ROOM"]["USER_LIST"][USER_NAME]
        await send_room_update(ROOM_CODE)
        print(f"Connection closed for user {USER_NAME} in room {ROOM_CODE}")
