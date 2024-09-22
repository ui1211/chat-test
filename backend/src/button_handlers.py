# %%

import asyncio
import random

from fastapi import WebSocket
from src.constants import (
    DEBUG,
    countdown_role_confirmation,
    countdown_role_execution,
    debugs,
    roles_dict,
)
from src.data_store import rooms
from src.helpers import current_time
from src.role_handlers import roleActionClass
from src.vote_handlers import voteManagerClass


class ButtonHandlerClass:
    """
    ボタン操作に関するクラス
    """

    def __init__(self, mamager):
        self.manager = mamager
        # self.room_manager = RoomManager(self.manager)
        self.role_action = roleActionClass(self.manager)
        self.vote_manager = voteManagerClass(self.manager)

    async def process_omakase_button(self, ROOM_CODE: str):
        """お任せボタンの押下時の処理

        Parameters
        ----------
        ROOM_CODE : str
            _description_
        """
        users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
        users_num = len(users) - 1  # USER_ID=100が存在するためマイナス-1

        if users_num == 3:
            role_list = ["20", "21", "21", "22", "23"]
        elif users_num == 4:
            role_list = ["20", "20", "21", "21", "22", "23"]
        elif users_num == 5:
            role_list = ["20", "20", "20", "21", "21", "22", "23"]
        elif users_num == 6:
            role_list = ["20", "20", "20", "20", "21", "21", "22", "23"]
        else:
            role_list = []

        rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"] = role_list
        await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S231")

    async def process_start_button(
        self,
        websocket: WebSocket,
        ROOM_CODE: int,
        USER_NAME: str,
        USER_ID: str,
    ):
        """スタートボタンの処理"""
        users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
        roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

        # 人数チェック(モック時は5人確定)
        valid_roles = [role for role in roles if role is not None]
        print(current_time(), f"役職一覧 room_code={ROOM_CODE} {valid_roles}")
        if len(valid_roles) < len(users):
            await self.manager.send_error_message(websocket, "S400", "M005", is_connected=True)
            return

        roles = [str(i) for i in roles]  # 役職IDを文字列に変換

        assigned_roles = self.assign_roles_to_users(users, roles)
        # print(current_time(), "assigned_roles", assigned_roles)
        rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
        # rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移
        # await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S232")

        # USERSのROLE_IDとROLE_NAMEを更新
        for user_id, role_data in assigned_roles.items():
            # print(user_id, role_data)
            if user_id in rooms[ROOM_CODE]["USERS"]:
                rooms[ROOM_CODE]["USERS"][user_id]["ROLE_ID"] = role_data["USER_ROLE1"]
                rooms[ROOM_CODE]["USERS"][user_id]["ROLE_NAME"] = roles_dict[role_data["USER_ROLE1"]]
                rooms[ROOM_CODE]["USERS"][user_id]["VISIBLE_LIST"].append(user_id)

        # 人狼のVISIBLE_LISTの更新
        werewolf_ids = [user_id for user_id, role_data in assigned_roles.items() if role_data["USER_ROLE1"] == "21"]
        for user_id in werewolf_ids:
            for other_werewolf_id in werewolf_ids:
                if user_id != other_werewolf_id:  # 自分以外の人狼を追加
                    rooms[ROOM_CODE]["USERS"][user_id]["VISIBLE_LIST"].append(other_werewolf_id)

        # 役職確認画面へ移行
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"
        await self.manager.send_room_update(ROOM_CODE, "S232")

        #
        from src.room_handlers import RoomManager

        room_manager = RoomManager(self.manager)

        # 役職確認画面(X秒)
        await room_manager.countdown_and_update(
            websocket,
            ROOM_CODE,
            USER_NAME,
            USER_ID,
            "R004",
            countdown=countdown_role_confirmation,
            loop_name="役職確認画面",
        )
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R004"
        await self.manager.send_room_update(ROOM_CODE, "S233")

        # 役職実行画面(X秒)
        await room_manager.countdown_and_update(
            websocket,
            ROOM_CODE,
            USER_NAME,
            USER_ID,
            "R005",
            countdown=countdown_role_execution,
            loop_name="役職実行画面",
        )
        await self.manager.send_room_update(ROOM_CODE, "S235")

        # カウントダウン後に自動で占い・怪盗のアクションを実行
        await self.role_action.auto_process_role_action(ROOM_CODE)  # S234を送信

        #
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R005"
        await self.manager.send_room_update(ROOM_CODE, "S210")
        #

        # プレイ画面、投票画面
        discussion_time = int(rooms[ROOM_CODE]["ROOM"]["ROOM_DISCUSSION_TIME"])
        await self.monitor_voting_and_discussion(
            room_manager,
            websocket,
            ROOM_CODE,
            USER_NAME,
            USER_ID,
            discussion_time,
        )
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R007"
        await self.manager.send_room_update(ROOM_CODE, "S260")  # 投票結果の処理を開始

        # 結果画面
        await self.vote_manager.determine_victory(ROOM_CODE)  # S261 投票結果の処理を完了

    async def monitor_voting_and_discussion(
        self, room_manager, websocket, ROOM_CODE, USER_NAME, USER_ID, discussion_time
    ):
        """議論時間と投票を並行して監視し、両方が完了したら次の処理に移行"""

        # 議論時間と全員投票の完了フラグ
        discussion_finished = False
        all_users_voted = False

        async def countdown_timer():
            """議論時間のカウントダウン処理"""
            nonlocal discussion_finished
            await room_manager.countdown_and_update(
                websocket,
                ROOM_CODE,
                USER_NAME,
                USER_ID,
                "",  # 議論時間中に次のステータスを設定しない
                countdown=discussion_time,
                loop_name="議論時間",
            )
            print(current_time(), f"議論時間が終了しました。room_code={ROOM_CODE}")
            rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R006"
            await self.manager.send_room_update(ROOM_CODE, "S238")  # 議論時間の終了
            discussion_finished = True

        async def voting_monitor():
            """全員の投票が完了するまで監視"""
            nonlocal all_users_voted
            while True:
                voted, _ = self.vote_manager.check_if_all_users_voted(ROOM_CODE)
                if voted:
                    print(current_time(), f"全員の投票が完了しました。room_code={ROOM_CODE}")
                    await self.manager.send_room_update(ROOM_CODE, "S252")  # 全員の投票が完了
                    all_users_voted = True
                    break
                await asyncio.sleep(1)  # 投票が完了するまで待機

        # 議論時間と投票監視を並行して実行
        await asyncio.gather(
            countdown_timer(),
            voting_monitor(),
        )

        # 議論時間が終了し、全員の投票が完了したら次の処理へ
        while not (discussion_finished and all_users_voted):
            await asyncio.sleep(0.5)  # 両方の完了を待機

        print(current_time(), f"議論時間と全員の投票が完了しました。room_code={ROOM_CODE}")

    async def process_end_button(self, WebSocket, room_code, user_name, user_id):
        print(current_time(), f"process_end_button: room_code={room_code} user_name={user_name}")

        from src.room_handlers import RoomManager

        room_manager = RoomManager(self.manager)
        await self.manager.send_room_update(room_code, STATUS_DETAIL_CODE="S237")
        await room_manager.handle_disconnect(WebSocket, room_code, user_name, user_id)

    async def process_exit_button(self, WebSocket, room_code, user_name, user_id):
        print(current_time(), f"process_exit_button: room_code={room_code} user_name={user_name}")

        from src.room_handlers import RoomManager

        room_manager = RoomManager(self.manager)
        await self.manager.send_room_update(room_code, STATUS_DETAIL_CODE="S236")
        await room_manager.handle_disconnect(WebSocket, room_code, user_name, user_id)
        # await room_manager.reassign_user_numbers(room_code)

    def assign_roles_to_users(self, users, roles):
        """ユーザーに役職を割り当て"""
        assigned_roles, i = {}, 0

        if DEBUG:
            assigned_roles = debugs["ROLE_LIST"]
        else:
            roles = random.sample(roles, len(roles))
            #
            print(current_time(), "assign_roles_to_users", roles)
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
