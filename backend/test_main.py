import asyncio
import json
from datetime import datetime

import websockets

print(str("===") * 10)
print(datetime.now())

# await asyncio.sleep(1)
users, users_num, send_flag, receive_flag = [], 5, True, True

# コマンドリスト
commands = {
    "cmd1": {
        "cmd": {"UPDATE": {"ROOM": {"ROOM_DISCUSSION_TIME": 999}}},  # 送信するコマンド
        "res": "S211",  # 想定されるレスポンス
        "send": False,  # コマンド送信したかどうか
        "display": False,  # テストケースで一度表示したか判定するフラグ
    },
    "cmd2": {
        "cmd": {"UPDATE": {"ROOM": {"ROOM_ROLE": [20, 20, 21, 22, None, None, None]}}},
        "res": "S212",
        "send": False,
        "display": False,
    },
    "cmd3": {
        "cmd": {"EVENT": "OMAKASE_BUTTON"},
        "res": "S231",
        "send": False,
        "display": False,
    },
    "cmd4": {
        "cmd": {"EVENT": "START_BUTTON"},
        "res": "S232",
        "send": False,
        "display": False,
    },
    "cmd5": {
        "cmd": {},  # スタートボタン押下後にカウントダウン終了時のメッセージを受け取る
        "res": "S233",
        "send": False,
        "display": False,
    },
}


def ppprint(header, response):
    print(datetime.now(), header, "\n", json.dumps(json.loads(response), indent=4, ensure_ascii=False), "\n")


async def create_room(user_name):
    global send_flag, receive_flag
    uri = f"ws://127.0.0.1:8000/ws/create/?USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri} as {user_name}\n")
        try:
            while True:
                response = await websocket.recv()
                response_json = json.loads(response)
                response_status = response_json["STATUS"]["STATUS_CODE"]

                # エラーメッセージ
                if response_status in ["S100", "S400"]:
                    ppprint(f"{uri}\n{response_status}", response)

                # ユーザ参加後の処理
                if len(users) == users_num:

                    # コマンドの数だけ処理
                    for key in commands.keys():
                        com = commands[key]

                        # イベント送信(一度だけ)
                        if com["send"] == False:
                            event = json.dumps(com["cmd"])
                            await websocket.send(event)
                            com["send"] = True

                        # イベント表示(一度だけ表示)
                        if com["display"] == False:
                            if response_status == com["res"]:
                                ppprint(f'{com["res"]}, {com["cmd"]}', response)
                                com["display"] = True

        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


async def join_room(room_code, user_name):
    uri = f"ws://127.0.0.1:8000/ws/join/?ROOM_CODE={room_code}&USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri} as {user_name}")
        try:
            while True:
                response = await websocket.recv()
                response_json = json.loads(response)
                response_status = response_json["STATUS"]["STATUS_CODE"]

                # エラーメッセージ
                if response_status in ["S100"]:
                    ppprint(f"{uri}\n{response_status}", response)

                if response_status == "S233":
                    ppprint(
                        "test",
                        json.dumps(
                            {
                                "USER": response_json["USER"],
                                "STATUS": response_json["STATUS"],
                            },
                            ensure_ascii=False,
                            indent=4,
                        ),
                    )

                # ppprint("join", response)
        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


# ==========main==========
async def main_check():
    print(str("******") * 10)
    print(datetime.now(), "main_check")

    room_code = 99999

    await asyncio.gather(
        create_room(user_name="fagi"),
        join_room(room_code=room_code, user_name="ui"),
        join_room(room_code=room_code, user_name="198"),
        join_room(room_code=room_code, user_name="mira"),
        join_room(room_code=room_code, user_name="cookie"),
    )


asyncio.run(main_check())
