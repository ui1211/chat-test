import asyncio
import json
import random
from datetime import datetime

import websockets
from test_command import creater_commands, joiner_commands_by_user


def current_time():
    return datetime.now().replace(microsecond=0)


def ppprint(header, response):
    """JSONデータを整形して表示"""
    if response:  # 空でないことを確認
        res = json.dumps(json.loads(response), indent=4, ensure_ascii=False)
        print(current_time(), header, "\n", res, "\n")
    else:
        print(current_time(), header, "\n", "Empty response\n")


simple = False  # 出力結果をSTATUSのみ


print(str("=======") * 10)
print(current_time())

# await asyncio.sleep(1)
users, users_num, send_flag, receive_flag = [], 5, True, True


async def execute_commands(websocket, commands, user_name):
    """共通のコマンド処理"""
    while True:
        response = await websocket.recv()

        response_json = json.loads(response)
        response_status = response_json["STATUS"]["STATUS_DETAIL_CODE"]

        # エラーメッセージ
        if response_status in ["S100", "S400"]:
            ppprint(f"Response: {response_status}", response)

        # コマンドの数だけ処理
        for key in commands.keys():
            com = commands[key]

            # イベント送信(一度だけ)
            if com["send"] == False:
                event = json.dumps(com["cmd"])
                # print("event", event)
                await websocket.send(event)
                com["send"] = True

            # イベント表示(一度だけ表示)
            if com["display"] == False:
                if simple:
                    res = json.dumps(response_json["STATUS"])
                else:
                    res = response
                # print(com["res"], response_status)
                # print(response_json["STATUS"])
                if response_status == com["res"]:
                    ppprint(f'{user_name}, {com["res"]}, {com["cmd"]}', res)
                    com["display"] = True


async def create_room(user_name, commands):
    uri = f"ws://127.0.0.1:8000/ws/create/?USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        try:
            if len(users) == users_num:
                # creater 用のコマンドを実行
                await execute_commands(websocket, commands, user_name)
        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


async def join_room(room_code, user_name, commands):
    uri = f"ws://127.0.0.1:8000/ws/join/?ROOM_CODE={room_code}&USER_NAME={user_name}"

    if user_name not in users:
        users.append(user_name)

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        try:
            # user_nameごとのコマンドを実行
            if user_name in commands:
                user_commands = joiner_commands_by_user[user_name]
                await execute_commands(websocket, user_commands, user_name)
        except websockets.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"An error occurred: {e}")


# ==========main==========
async def main_check():

    print(current_time(), "main_check")

    room_code = 99999

    await asyncio.gather(
        create_room(user_name="fagi", commands=creater_commands),
        join_room(room_code=room_code, user_name="ui", commands=joiner_commands_by_user),
        join_room(room_code=room_code, user_name="198", commands=joiner_commands_by_user),
        join_room(room_code=room_code, user_name="mira", commands=joiner_commands_by_user),
        join_room(room_code=room_code, user_name="cookie", commands=joiner_commands_by_user),
    )


async def exit_scenario():

    print(current_time(), "exit_scenario")

    room_code = 99999

    creater_commands = {}
    joiner_commands_by_user_ = {
        "ui": {
            "cmd1": {
                "cmd": {"EVENT": "EXIT_BUTTON"},
                "res": "S200",
                "send": False,
                "display": False,
            },
        },
    }

    # ルーム参加者のユーザ名、ルームコードが不正確
    await asyncio.gather(
        create_room(user_name="fagi", commands=creater_commands),
        join_room(room_code=room_code, user_name="ui", commands=joiner_commands_by_user_),
        join_room(room_code=room_code, user_name="198", commands=joiner_commands_by_user_),
    )


# asyncio.run(main_check())
asyncio.run(exit_scenario())
