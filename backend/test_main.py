import asyncio
import json
import random
from datetime import datetime

import websockets
from test_command import creater_commands, joiner_commands_by_user

print(str("===") * 10)
print(datetime.now())

# await asyncio.sleep(1)
users, users_num, send_flag, receive_flag = [], 5, True, True


def ppprint(header, response):
    print(datetime.now(), header, "\n", json.dumps(json.loads(response), indent=4, ensure_ascii=False), "\n")


async def execute_commands(websocket, commands):
    """共通のコマンド処理"""
    while True:
        response = await websocket.recv()
        response_json = json.loads(response)
        response_status = response_json["STATUS"]["STATUS_CODE"]

        # エラーメッセージ
        if response_status in ["S100", "S400"]:
            ppprint(f"Response: {response_status}", response)

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


async def create_room(user_name):
    uri = f"ws://127.0.0.1:8000/ws/create/?USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri} as {user_name}\n")
        try:
            if len(users) == users_num:
                # creater 用のコマンドを実行
                await execute_commands(websocket, creater_commands)
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
            # user_nameごとのコマンドを実行
            if user_name in joiner_commands_by_user:
                user_commands = joiner_commands_by_user[user_name]
                await execute_commands(websocket, user_commands)
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
