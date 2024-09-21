# %%

import asyncio
import random

from fastapi import WebSocket
from src.constants import DEBUG, countdown_role_confirmation, debugs, roles_dict
from src.data_store import rooms
from src.helpers import current_time


class ButtonHandlerClass:
    """
    ボタン操作に関するクラス
    """

    def __init__(self, mamager):
        self.manager = mamager

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

    async def process_start_button(self, websocket: WebSocket, ROOM_CODE: int):
        """スタートボタンの処理"""
        users = rooms[ROOM_CODE]["ROOM"]["ROOM_USER"]
        roles = rooms[ROOM_CODE]["ROOM"]["ROOM_ROLE"]

        # 人数チェック(モック時は5人確定)
        valid_roles = [role for role in roles if role is not None]
        print(current_time(), "valid_roles", valid_roles)
        if len(valid_roles) < len(users):
            await self.manager.send_error_message(websocket, "S400", "M005", is_connected=True)
            return

        roles = [str(i) for i in roles]  # 役職IDを文字列に変換

        assigned_roles = self.assign_roles_to_users(users, roles)
        print(current_time(), "assigned_roles", assigned_roles)
        rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"] = assigned_roles
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R003"  # 役職確認画面に遷移

        # USERSのROLE_IDとROLE_NAMEを更新
        for user_id, role_data in assigned_roles.items():
            print(user_id, role_data)
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

        # 役職確認フェーズへ移行

        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R004"

        await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S232")

        # 役職確認画面
        await self.countdown_and_update(
            ROOM_CODE, ROOM_STATUS="R005", STATUS_DETAIL_CODE="S233", countdown=countdown_role_confirmation
        )

        # 役職実行画面
        # await countdown_and_update(
        #     ROOM_CODE,
        #     ROOM_STATUS="R005",
        #     STATUS_DETAIL_CODE="S235",
        #     countdown=countdown_role_execution,
        # )

        # カウントダウン後に自動で占い・怪盗のアクションを実行
        # await auto_process_role_action(ROOM_CODE)
        #

    def process_end_button(self):
        pass

    async def process_exit_button(self, room_code, user_name, user_id):

        from src.room_handlers import RoomManager

        room_manager = RoomManager(self.manager)
        await room_manager.handle_disconnect(user_name, room_code, user_id)
        await room_manager.reassign_user_numbers(room_code)

    async def countdown_and_update(self, ROOM_CODE: int, ROOM_STATUS: str, STATUS_DETAIL_CODE: str, countdown: int):
        """カウントダウンを行い、ルーム状態を更新"""
        for i in range(countdown, 0, -1):
            print(f"countdown_role_confirmation: {i} seconds remaining...")
            await asyncio.sleep(1)
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = ROOM_STATUS  # 役職実行画面に遷移
        await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE=STATUS_DETAIL_CODE)

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
