import asyncio
import json
from datetime import datetime

import websockets
from scenarios.disconnect_creater import disconnect_creater_scenario
from scenarios.disconnect_joiner import disconnect_joiner_scenario
from scenarios.join_errors import join_error_scenario
from scenarios.normal_play import normal_play_scenario
from scenarios.revote_test import revote_test_scenario
from scenarios.win_villager import win_villager_scenario
from scenarios.win_werewolf import win_werewolf_scenario

simple = False


def current_time():
    return datetime.now().replace(microsecond=0)


def ppprint(header, response):
    """JSONデータを整形して表示"""
    if response:  # 空でないことを確認
        res = json.dumps(json.loads(response), indent=4, ensure_ascii=False)
        print(current_time(), header, "\n", res, "\n")
    else:
        print(current_time(), header, "\n", "Empty response\n")


async def execute_scenario(websocket, command_key, command_info):
    """特定のコマンドを処理"""
    if not command_info["command_sended"]:
        # コマンド送信前の待機時間
        await asyncio.sleep(command_info["wait_time"])
        await websocket.send(json.dumps(command_info["command"]))
        command_info["command_sended"] = True
        print(f"Command sent from {command_info['user_name']}: {command_info['command']}")

    while not command_info["response_displayed"]:
        response = await websocket.recv()
        response_json = json.loads(response)
        response_status = response_json["STATUS"]["STATUS_DETAIL_CODE"]

        # レスポンスが指定のステータスコードに一致する場合
        if response_status == command_info["request_status_code"]:
            if simple:
                response = json.dumps(response_json["STATUS"])
            ppprint(f"Response for {command_info['user_name']} key={command_key}", response)
            command_info["response_displayed"] = True
            break  # 次のコマンドに進む


async def process_commands(commands):
    # WebSocket接続をユーザーごとに開く
    user_websockets = {}

    try:
        for command_key, command_info in commands.items():
            user_name = command_info["user_name"]

            if user_name not in user_websockets:
                # 各コマンドの `uri` キーからWebSocket接続を開く
                uri = command_info["uri"]
                websocket = await websockets.connect(uri)
                user_websockets[user_name] = websocket
                print(f"Connected to {uri} for {user_name}")

            # 各コマンドを順番に処理
            await execute_scenario(user_websockets[user_name], command_key, command_info)

    finally:
        # 全てのWebSocket接続をクローズ
        for websocket in user_websockets.values():
            await websocket.close()


# 実行
# asyncio.run(process_commands(join_error_scenario))
# asyncio.run(process_commands(disconnect_joiner_scenario))
# asyncio.run(process_commands(disconnect_creater_scenario))
# asyncio.run(process_commands(revote_test_scenario))
# asyncio.run(process_commands(normal_play_scenario))
# asyncio.run(process_commands(win_werewolf_scenario))

asyncio.run(process_commands(win_villager_scenario))
