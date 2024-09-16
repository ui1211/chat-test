import asyncio
import json
import random
from datetime import datetime
from pprint import pprint

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

##
from src.constants import (
    ALLOWED_COMMANDS,
    codes,
    countdown_role_confirmation,
    countdown_role_execution,
    debugs,
    messages,
    roles_dict,
)
from src.data_store import rooms
from src.manager import ConnectionManager
from src.templates import ROOM_TEMPLATE, USER_TEMPLATE

DEBUG = True

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
        # print(datetime.now(), f"send in ROOM_CODE : {ROOM_CODE}")
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
                    #
                elif role_id == "21":  # 人狼
                    MESSAGE_CODE = "M101"
                    #
                elif role_id == "22":  # 占い師
                    MESSAGE_CODE = "M102"
                    # 例: 占い師の特殊処理をここで追加
                elif role_id == "23":  # 怪盗
                    MESSAGE_CODE = "M103"
                    # 例: 怪盗の特殊処理をここで追加

            elif ROOM_STATUS == "R005":  # プレイ画面
                # 必要に応じて処理を追加
                pass

            elif ROOM_STATUS == "R006":  # 投票画面
                pass

            elif ROOM_STATUS == "R007":  # 結果画面
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
                # print(datetime.now(), f"send in ROOM_CODE : {ROOM_CODE}, for USER_NAME: {USER_NAME}")
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


async def check_and_update_if_all_roles_finished(ROOM_CODE: int):
    """全ユーザーのROLE_FINがTrueかチェックし、全員完了していたらsend_room_updateを実行"""
    room_roles = rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"]

    # 全ユーザーのROLE_FINがTrueかをチェック
    all_finished = all(user_data.get("ROLE_FIN", False) for user_data in room_roles.values())

    if all_finished:
        print("All users have finished their roles.")
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R005"
        await send_room_update(ROOM_CODE, STATUS_CODE="S234")  # 全員完了後のステータスコードを設定
    else:
        print("Some users are still not finished with their roles.")


# ==========BUTTON==========


async def handle_event(websocket: WebSocket, message_data, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """イベントを処理"""
    event_type = message_data["EVENT"]

    if event_type == "OMAKASE_BUTTON":
        await process_omakase_button(ROOM_CODE)
    elif event_type == "START_BUTTON":
        await process_start_button(websocket, ROOM_CODE)
    elif event_type == "END_BUTTON":
        await process_end_button(USER_NAME, ROOM_CODE, USER_ID)
    else:
        print(f"Unknown event type: {event_type}")


async def countdown_and_update(ROOM_CODE: int, ROOM_STATUS: str, STATUS_CODE: str, countdown: int):
    """カウントダウンを行い、ルーム状態を更新"""
    for i in range(countdown, 0, -1):
        print(f"countdown_role_confirmation: {i} seconds remaining...")
        await asyncio.sleep(1)
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = ROOM_STATUS  # 役職実行画面に遷移
    await send_room_update(ROOM_CODE, STATUS_CODE=STATUS_CODE)


async def process_omakase_button(ROOM_CODE: int):
    """おまかせボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    users_num = len(users) - 1

    if users_num == 3:
        role_list = ["20", "21", "21", "22", "23"]
    elif users_num == 4:
        role_list = ["20", "20", "21", "21", "22", "23"]
    elif users_num == 5:
        role_list = ["20", "20", "20", "21", "21", "22", "23"]
    elif users_num == 6:
        role_list = ["20", "20", "20", "20", "21", "21", "22", "23"]

    rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"] = role_list
    await send_room_update(ROOM_CODE, STATUS_CODE="S231")


async def process_start_button(websocket: WebSocket, ROOM_CODE: int):
    """スタートボタンの処理"""
    users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
    roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

    # 人数チェック(モック時は5人確定)
    valid_roles = [role for role in roles if role is not None]
    print(datetime.now(), "valid_roles", valid_roles)
    if len(valid_roles) < len(users):
        await send_error_message(websocket, "S400", "M005", is_connected=True)
        return

    roles = [str(i) for i in roles]  # 役職IDを文字列に変換

    assigned_roles = assign_roles_to_users(users, roles)
    print(datetime.now(), "assigned_roles", assigned_roles)
    rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移

    # USERSのROLE_IDとROLE_NAMEを更新
    for user_id, role_data in assigned_roles.items():
        if user_id in rooms[ROOM_CODE]["USERS"]:
            rooms[ROOM_CODE]["USERS"][user_id]["ROLE_ID"] = role_data["USER_ROLE1"]
            rooms[ROOM_CODE]["USERS"][user_id]["ROLE_NAME"] = roles_dict[role_data["USER_ROLE1"]]
            rooms[ROOM_CODE]["USERS"][user_id]["VISIBLE_LIST"].append(user_id)  # 自身を表示ユーザに追加

    # 人狼のVISIBLE_LISTの更新
    werewolf_ids = [user_id for user_id, role_data in assigned_roles.items() if role_data["USER_ROLE1"] == "21"]
    for user_id in werewolf_ids:
        for other_werewolf_id in werewolf_ids:
            if user_id != other_werewolf_id:  # 自分以外の人狼を追加
                rooms[ROOM_CODE]["USERS"][user_id]["VISIBLE_LIST"].append(other_werewolf_id)

    # 役職確認フェーズへ移行
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R004"
    await send_room_update(ROOM_CODE, STATUS_CODE="S232")

    # 役職確認画面
    await countdown_and_update(
        ROOM_CODE,
        ROOM_STATUS="R005",
        STATUS_CODE="S233",
        countdown=countdown_role_confirmation,
    )

    # 役職実行画面
    # await countdown_and_update(
    #     ROOM_CODE,
    #     ROOM_STATUS="R005",
    #     STATUS_CODE="S235",
    #     countdown=countdown_role_execution,
    # )

    # カウントダウン後に自動で占い・怪盗のアクションを実行
    # await auto_process_role_action(ROOM_CODE)
    #


async def process_end_button(USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """エンドボタンの処理"""
    await handle_disconnect(USER_NAME, ROOM_CODE, USER_ID)


# ==========勝利判定==========
async def determine_victory(ROOM_CODE: int):
    """勝利条件の判定"""
    room_data = rooms[ROOM_CODE]
    role_list = room_data["ROLE"]["ROLE_LIST"]

    # 人狼陣営と村人陣営のプレイヤーを取得
    werewolves = [user_id for user_id, role_data in role_list.items() if role_data["USER_ROLE1"] == "21"]
    villagers = [user_id for user_id, role_data in role_list.items() if role_data["USER_ROLE1"] == "20"]

    # 投票結果から処刑されたユーザーを取得
    voted_out_user_id = await get_voted_out_user(ROOM_CODE)

    # 初期化: 陣営とユーザIDリストをRESULTに追加
    room_data["RESULT"]["RESULT_TEXT"] = ""
    room_data["RESULT"]["VOTE_RESULT"] = {}
    room_data["RESULT"]["USER_ID_LIST"] = []

    # 村人陣営の勝利条件
    if len(werewolves) == 0:
        print(f"Room {ROOM_CODE}: 村人陣営の勝利 (人狼がいないため)")
        room_data["ROOM"]["VICTORY"] = "villager"
        room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
        room_data["RESULT"]["USER_ID_LIST"] = villagers  # 村人陣営のユーザーIDをリストに追加

    elif voted_out_user_id in werewolves:
        print(f"Room {ROOM_CODE}: 村人陣営の勝利 (人狼が処刑された)")
        room_data["ROOM"]["VICTORY"] = "villager"
        room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
        room_data["RESULT"]["USER_ID_LIST"] = villagers  # 村人陣営のユーザーIDをリストに追加

    # 人狼陣営の勝利条件
    elif voted_out_user_id not in werewolves and len(werewolves) > 0:
        print(f"Room {ROOM_CODE}: 人狼陣営の勝利")
        room_data["ROOM"]["VICTORY"] = "werewolf"
        room_data["RESULT"]["RESULT_TEXT"] = "人狼陣営の勝利"
        room_data["RESULT"]["USER_ID_LIST"] = werewolves  # 人狼陣営のユーザーIDをリストに追加

    # # # 特殊陣営（怪盗など）の勝利条件（例）
    # for user_id, role_data in role_list.items():
    #     if role_data["USER_ROLE1"] == "23":  # 怪盗
    #         if check_thief_victory(user_id, room_data):
    #             room_data["ROOM"]["VICTORY"] = "thief"
    #             room_data["RESULT"]["RESULT_TEXT"] = "怪盗が勝利しました"
    #             room_data["RESULT"]["USER_ID_LIST"].append(user_id)  # 怪盗のユーザーIDをリストに追加
    #             print(f"Room {ROOM_CODE}: 怪盗が勝利しました")
    #             # return

    # デフォルトで村人陣営を勝利に設定（勝利条件が満たされなかった場合）
    if "VICTORY" not in room_data["ROOM"]:
        print(f"Room {ROOM_CODE}: 村人陣営の勝利 (デフォルト)")
        room_data["ROOM"]["VICTORY"] = "villager"
        room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
        room_data["RESULT"]["USER_ID_LIST"] = villagers  # 村人陣営のユーザーIDをリストに追加

    # 投票結果をVOTE_RESULTに記載
    room_data["RESULT"]["VOTE_RESULT"] = await get_vote_results(ROOM_CODE)
    print(f"Vote results: {room_data['RESULT']['VOTE_RESULT']}")

    await send_room_update(ROOM_CODE, STATUS_CODE="S261")


async def get_voted_out_user(ROOM_CODE: int):
    """投票によって処刑されたユーザーを取得する関数"""
    room_data = rooms[ROOM_CODE]
    vote_counts = {}

    # 投票の集計
    for user_id, user_data in room_data["USERS"].items():
        voted_for = user_data.get("USER_VOTE")
        if voted_for:
            if voted_for not in vote_counts:
                vote_counts[voted_for] = 0
            vote_counts[voted_for] += 1

    # 最も多く投票されたユーザーを取得
    if vote_counts:
        voted_out_user_id = max(vote_counts, key=vote_counts.get)
        print(f"User {voted_out_user_id} has been voted out.")
        return voted_out_user_id
    return None


async def get_vote_results(ROOM_CODE: int) -> dict:
    """投票結果を集計し、VOTE_RESULTに記載"""
    room_data = rooms[ROOM_CODE]
    vote_results = {}

    # 投票の集計
    for user_id, user_data in room_data["USERS"].items():
        voted_for = user_data.get("USER_VOTE")
        if voted_for:
            if voted_for not in vote_results:
                vote_results[voted_for] = []
            vote_results[voted_for].append(user_id)

    return vote_results


def check_thief_victory(user_id: int, room_data: dict) -> bool:
    """怪盗の勝利条件を判定する関数"""
    # 実装例：怪盗が盗んだ役職によって勝利条件を判定
    thief_role = room_data["ROLE"]["ROLE_LIST"][user_id]["USER_ROLE2"]  # 怪盗が盗んだ役職
    if thief_role == "21":  # 例: 怪盗が人狼になった場合、人狼陣営に勝利を移す
        return True
    return False


# ==========ROLE==========


def assign_roles_to_users(users, roles):
    """ユーザーに役職を割り当て"""
    assigned_roles, i = {}, 0

    if DEBUG:
        assigned_roles = debugs["ROLE_LIST"]
    else:
        roles = random.sample(roles, len(roles))
        #
        print(datetime.now(), "assign_roles_to_users", roles)
        for user_id, user_name in users.items():
            if False:
                pass
                # TODO 後ほどバナナを実装
            elif user_id == "100":
                continue
            else:
                role = roles[i]
                i += 1
            #
            if role in ["20", "21"]:
                role_fin = True
            else:
                role_fin = False

            assigned_roles[str(user_id)] = {
                "USER_NAME": user_name,
                "USER_ROLE1": role,
                "USER_ROLE2": role,
                "ROLE_FIN": role_fin,
            }

        #
        assigned_roles["100"] = {
            "USER_NAME": None,
            "USER_ROLE1": roles[i],
            "USER_ROLE2": roles[i + 1],
            "ROLE_FIN": True,  # 役職行動は完了しているとする
        }

    return assigned_roles


async def auto_process_role_action(ROOM_CODE: int):
    """占い師や怪盗がアクションを実行していない場合、自動的に処理する"""
    room_roles = rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"]
    user_ids = list(room_roles.keys())

    for user_id, role_data in room_roles.items():
        print(datetime.now(), "auto_process_role_action", user_id, role_data, role_data.get("ROLE_FIN"))
        role_id = role_data["USER_ROLE1"]
        # print(role_id)

        if role_id == "22" and not role_data.get("ROLE_FIN"):  # 占い師がまだアクションを実行していない場合
            target_user_id = random.choice([uid for uid in user_ids if uid != user_id])  # 自分以外の対象を選択
            await execute_fortune_teller(ROOM_CODE, user_id, target_user_id)

        elif role_id == "23" and not role_data.get("ROLE_FIN"):  # 怪盗がまだアクションを実行していない場合
            target_user_id = random.choice([uid for uid in user_ids if uid != user_id and uid != "100"])
            await execute_thief(ROOM_CODE, user_id, target_user_id)

    await check_and_update_if_all_roles_finished(ROOM_CODE)


async def role_action_process(role_data: dict, ROOM_CODE: int, USER_ID: int):
    if "FORTUNE_TELL" in role_data:
        user_id_to_fortune_tell = role_data["FORTUNE_TELL"]
        await execute_fortune_teller(ROOM_CODE, USER_ID, user_id_to_fortune_tell)
    elif "THIEF" in role_data:
        user_id_to_steal = role_data["THIEF"]
        await execute_thief(ROOM_CODE, USER_ID, user_id_to_steal)

    await check_and_update_if_all_roles_finished(ROOM_CODE)


## 占い師
async def execute_fortune_teller(ROOM_CODE: int, USER_ID: int, target_user_id: int):
    print(datetime.now(), "execute_fortune_teller", ROOM_CODE, USER_ID, target_user_id)
    room = rooms[ROOM_CODE]
    target_user_id = str(target_user_id)
    if target_user_id in room["ROLE"]["ROLE_LIST"]:
        target_role = room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE1"]
        target_role_name = roles_dict.get(str(target_role), "不明な役職")
        room["ROLE"]["FORTUNE_TELL"] = target_user_id
        room["ROLE"]["ROLE_LIST"][USER_ID]["ROLE_FIN"] = True
        #
        room["USERS"][USER_ID]["VISIBLE_LIST"].append(target_user_id)
        print(f"占い師はユーザーID {target_user_id} の役職 {target_role_name} を確認しました。")
        await send_room_update(ROOM_CODE, STATUS_CODE="S243")
    else:
        print(f"ユーザーID {target_user_id} はルームに存在しません。")
        # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} は存在しません。"


## 怪盗
async def execute_thief(ROOM_CODE: int, USER_ID: int, target_user_id: int):
    print(datetime.now(), "execute_thief", ROOM_CODE, USER_ID, target_user_id)
    room = rooms[ROOM_CODE]
    USER_ID = str(USER_ID)  # USER_IDを文字列に変換
    target_user_id = str(target_user_id)  # target_user_idを文字列に変換

    # 両方のユーザーが存在するか確認
    if USER_ID in room["ROLE"]["ROLE_LIST"] and target_user_id in room["ROLE"]["ROLE_LIST"]:
        # USER_ROLE2を入れ替え
        user_role2 = room["ROLE"]["ROLE_LIST"][USER_ID]["USER_ROLE2"]
        target_role2 = room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE2"]

        # 入れ替えを実行
        room["ROLE"]["ROLE_LIST"][USER_ID]["USER_ROLE2"] = target_role2
        room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE2"] = user_role2

        # 怪盗の行動を記録
        room["ROLE"]["THIEF"] = target_user_id
        room["ROLE"]["ROLE_LIST"][USER_ID]["ROLE_FIN"] = True

        #
        room["USERS"][USER_ID]["VISIBLE_LIST"].append(target_user_id)

        # 状態の更新をクライアントに通知
        await send_room_update(ROOM_CODE, STATUS_CODE="S244")
    else:
        print(f"ユーザーID {USER_ID} またはターゲットユーザーID {target_user_id} が存在しません。")


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


async def handle_update_command(message_data, ROOM_CODE: int, USER_ID: int):
    """更新コマンドの処理と通知"""
    update_data = message_data.get("UPDATE")
    print(datetime.now(), update_data)
    if update_data:
        if "ROLE" in update_data:
            await role_action_process(update_data["ROLE"], ROOM_CODE, USER_ID)
        else:
            # 許可されたキーを更新し、変更があった場合のみ send_room_update を発砲
            updated, status_code = selective_recursive_update(rooms[ROOM_CODE], update_data)
            if updated:
                # ステータスコードがある場合に send_room_update に渡す
                await send_room_update(ROOM_CODE, STATUS_CODE=status_code)
    else:
        await manager.broadcast(json.dumps({"STATUS": {"STATUS_CODE": "E999"}}), ROOM_CODE)


async def handle_vote():
    pass


async def handle_websocket_communication(websocket: WebSocket, USER_NAME: str, ROOM_CODE: int, USER_ID: int):
    """WebSocket通信の処理"""
    while True:
        data = await websocket.receive_text()
        try:
            message_data = json.loads(data)
            if "MANAGE" in message_data:
                await send_room_update(ROOM_CODE, STATUS_CODE="S200")
            elif "UPDATE" in message_data:
                await handle_update_command(message_data, ROOM_CODE, USER_ID)
            elif "EVENT" in message_data:
                await handle_event(websocket, message_data, USER_NAME, ROOM_CODE, USER_ID)
            elif "VOTE" in message_data:
                await handle_vote_command(message_data, ROOM_CODE, USER_ID)
            else:
                print(f"Received invalid data: {data}")

        except ValueError:
            print(f"Error processing message from {USER_NAME} in room {ROOM_CODE}: {data}")


# ==========VOTE==========


async def handle_vote_command(message_data: dict, ROOM_CODE: int, USER_ID: int):
    """VOTE処理: 投票情報を更新し、全員の投票が完了したか確認する"""
    room_data = rooms[ROOM_CODE]
    user_data = room_data["USERS"][USER_ID]
    vote_data = message_data.get("VOTE")

    # 投票先ユーザIDを取得
    vote_target_id = str(vote_data.get("USER_ID"))

    if vote_target_id:
        # 投票先を更新
        user_data["USER_VOTE"] = vote_target_id
        # 投票済みユーザIDを更新
        room_data["ROOM"]["VOTED_USER_LIST"].append(USER_ID)
        room_data["ROOM"]["ROOM_STATUS"] = "R006"
        await send_room_update(ROOM_CODE, STATUS_CODE="S251")

        print(f"User {USER_ID} voted for {vote_target_id}")

        # 全員の投票が完了したかを確認
        all_users_voted = check_if_all_users_voted(ROOM_CODE)
        if all_users_voted:
            print(f"All users in room {ROOM_CODE} have voted.")
            await proceed_to_next_phase(ROOM_CODE)
            await determine_victory(ROOM_CODE)
        else:
            print(f"Waiting for more users to vote in room {ROOM_CODE}.")
    else:
        print(f"Invalid vote data: {message_data}")


def check_if_all_users_voted(ROOM_CODE: int) -> bool:
    """全ユーザーが投票を完了したかチェック"""
    room_data = rooms[ROOM_CODE]
    total_users = len(room_data["USERS"])
    voted_users = len(room_data["ROOM"]["VOTED_USER_LIST"])

    # 全ユーザーが投票した場合にTrueを返す
    return voted_users >= total_users


async def proceed_to_next_phase(ROOM_CODE: int):
    """全員の投票が完了したら次のフェーズに進む処理"""
    # 投票結果の集計などを行うフェーズ
    print(f"Proceeding to the next phase in room {ROOM_CODE}...")

    # 例: 結果発表フェーズへ移行
    rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R007"  # 結果発表画面
    await send_room_update(ROOM_CODE, STATUS_CODE="S252")


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

    if DEBUG:
        ROOM_CODE = debugs["ROOM_CODE"]
        USER_ID = debugs["USER_ID"][USER_NAME]
    else:
        ROOM_CODE = str(random.randint(10000, 99999))
        USER_ID = str(random.randint(200, 999))

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
    if DEBUG:
        USER_ID = debugs["USER_ID"][USER_NAME]
    else:
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
