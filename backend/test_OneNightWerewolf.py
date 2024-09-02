import asyncio
import json
import time

import websockets

# 状態を共有するためのロック
lock = asyncio.Lock()
users = []

#
route = "ROOM_ROLE"


async def create_room(user_name):
    """
    WebSocket client to create a room.
    """
    uri = f"ws://127.0.0.1:8000/ws/create/?USER_NAME={user_name}"
    async with websockets.connect(uri) as websocket:
        # サーバーからのメッセージを受信
        response = await websocket.recv()
        print(f"Creator received:\n {response}\n")

        # ユーザーを追加し、ユーザーリストを同期的に更新
        async with lock:
            users.append(user_name)

        # try:
        while True:
            await asyncio.sleep(1)

            # 全てのユーザーが参加したらイベントを実行
            async with lock:
                if len(users) == 3:
                    await asyncio.sleep(1)
                    # 更新:議論時間
                    event = json.dumps({"UPDATE": {"ROOM": {"ROOM_DISCUSSION_TIME": 999}}})
                    await websocket.send(event)
                    res = await websocket.recv()
                    print(f"Sent UPDATE:ROOM_DISCUSSION_TIME, received:\n {res}\n")

                    # 更新: ルーム役職役職
                    event = json.dumps({"UPDATE": {"ROOM": {"ROOM_ROLE": [None, None, None, None, None]}}})
                    await websocket.send(event)
                    res = await websocket.recv()
                    print(f"Sent UPDATE:ROOM_ROLE, received:\n {res}\n")

                    # イベント:お任せボタン
                    event = json.dumps({"EVENT": "OMAKASE_BUTTON"})
                    await websocket.send(event)
                    res = await websocket.recv()
                    print(f"Sent OMAKASE_BUTTON, received:\n {res}\n")

                    # イベント:スタートボタン
                    event = json.dumps({"EVENT": "START_BUTTON"})
                    await websocket.send(event)
                    res = await websocket.recv()
                    print(f"Sent START_BUTTON, received:\n {res}\n")

                    break

        while True:
            await asyncio.sleep(1)
            res = await websocket.recv()
            print(res, "\n")


async def join_room(room_code, user_name):
    """
    WebSocket client to join a room.
    """
    uri = f"ws://127.0.0.1:8000/ws/join/?ROOM_CODE={room_code}&USER_NAME={user_name}"
    async with websockets.connect(uri) as websocket:
        # try:
        while True:
            await asyncio.sleep(0.5)
            # サーバーからのメッセージを受信
            response = json.loads(await websocket.recv())

            if len(users) < 3:
                if response["STATUS"]["STATUS_CODE"] == "S200":
                    print(f"Joiner {user_name} received:\n {response}\n")
                    # ユーザーを追加し、ユーザーリストを同期的に更新
                    async with lock:
                        users.append(user_name)


async def main():
    # 部屋を作成し、ユーザーを参加させる並列タスクを設定
    creator_task = asyncio.create_task(create_room("Alice"))

    room_code = 999999  # テスト用のダミーのルームコード
    joiner_task1 = asyncio.create_task(join_room(room_code, "Bob"))
    joiner_task2 = asyncio.create_task(join_room(room_code, "Cyn"))

    # 並列でタスクを実行
    await asyncio.gather(creator_task, joiner_task1, joiner_task2)


# メイン関数を実行
asyncio.run(main())
