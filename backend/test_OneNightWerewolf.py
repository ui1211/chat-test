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
        "res": "S210",  # 想定されるレスポンス
        "display": False,  # テストケースで一度表示したか判定するフラグ
    },
    "cmd2": {
        "cmd": {"UPDATE": {"ROOM": {"ROOM_ROLE": [20, 20, 21, 22, None, None, None]}}},
        "res": "S210",
        "display": False,
    },
    "cmd3": {
        "cmd": {"EVENT": "OMAKASE_BUTTON"},
        "res": "S211",
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
                # ppprint("create", response_json)

                # イベント送信
                if len(users) == users_num and send_flag == True:
                    #
                    event = json.dumps({"UPDATE": {"ROOM": {"ROOM_DISCUSSION_TIME": 999}}})
                    print(datetime.now(), "send", event)
                    await websocket.send(event)

                    #
                    # event = json.dumps({"EVENT": "OMAKASE_BUTTON"})
                    # print(datetime.now(), "send", event)
                    # await websocket.send(event)

                    #
                    send_flag = False  # 送信を一度だけ行うためのフラグ

                # イベント取得
                if send_flag == False and receive_flag == True:
                    if response_json["STATUS"]["STATUS_CODE"] == "S210":  # UPDATEコマンドの成功を監視
                        ppprint("receive S210", response)

                        receive_flag = False  # 表示を一度だけ行うためのフラグ

        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


async def join_room(room_code, user_name):
    uri = f"ws://127.0.0.1:8000/ws/join/?ROOM_CODE={room_code}&USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri} as {user_name}\n")
        try:
            while True:
                response = await websocket.recv()
                # ppprint("join", response)
        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


async def main():
    room_code = 99999

    await asyncio.gather(
        create_room(user_name="fagi"),
        join_room(room_code=room_code, user_name="ui"),
        join_room(room_code=room_code, user_name="198"),
        join_room(room_code=room_code, user_name="mira"),
        join_room(room_code=room_code, user_name="cookie"),
    )


asyncio.run(main())
