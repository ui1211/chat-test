import random

from src.constants import roles_dict
from src.data_store import rooms
from src.helpers import current_time


class roleActionClass:
    def __init__(self, manager):
        self.manager = manager
        self.roles_dict = roles_dict

    async def role_action_process(self, role_data: dict, ROOM_CODE: int, USER_ID: int):
        if "FORTUNE_TELL" in role_data:
            user_id_to_fortune_tell = role_data["FORTUNE_TELL"]
            await self.execute_fortune_teller(ROOM_CODE, USER_ID, user_id_to_fortune_tell)
        elif "THIEF" in role_data:
            user_id_to_steal = role_data["THIEF"]
            await self.execute_thief(ROOM_CODE, USER_ID, user_id_to_steal)

        await self.check_and_update_if_all_roles_finished(ROOM_CODE)

    ## 占い師
    async def execute_fortune_teller(self, ROOM_CODE: int, USER_ID: int, target_user_id: int):
        print(current_time(), "execute_fortune_teller", ROOM_CODE, USER_ID, target_user_id)
        room = rooms[ROOM_CODE]
        target_user_id = str(target_user_id)
        # print(room["ROLE"]["ROLE_LIST"])
        if target_user_id in room["ROLE"]["ROLE_LIST"]:
            target_role = room["ROLE"]["ROLE_LIST"][target_user_id]["USER_ROLE1"]
            target_role_name = roles_dict.get(str(target_role), "不明な役職")
            room["ROLE"]["FORTUNE_TELL"] = target_user_id
            room["ROLE"]["ROLE_LIST"][USER_ID]["ROLE_FIN"] = True
            #
            room["USERS"][USER_ID]["VISIBLE_LIST"].append(target_user_id)
            print(current_time(), f"占い師はユーザーID {target_user_id} の役職 {target_role_name} を確認しました。")
            await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S243")
        else:
            print(current_time(), f"ユーザーID {target_user_id} はルームに存在しません。")
            # room["RESULT"]["RESULT_TEXT"] = f"ユーザーID {target_user_id} は存在しません。"

    ## 怪盗
    async def execute_thief(self, ROOM_CODE: int, USER_ID: int, target_user_id: int):
        print(current_time(), "execute_thief", ROOM_CODE, USER_ID, target_user_id)
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
            await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S244")
        else:
            print(current_time(), f"ユーザーID {USER_ID} またはターゲットユーザーID {target_user_id} が存在しません。")

    async def check_and_update_if_all_roles_finished(self, ROOM_CODE: int):
        """全ユーザーのROLE_FINがTrueかチェックし、全員完了していたらsend_room_updateを実行"""
        room_roles = rooms[ROOM_CODE]["ROLE"]["ROLE_LIST"]

        # 全ユーザーのROLE_FINがTrueかをチェック
        all_finished = all(user_data.get("ROLE_FIN", False) for user_data in room_roles.values())

        if all_finished:
            print(current_time(), "All users have finished their roles.")
            rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R005"
            await self.manager.send_room_update(
                ROOM_CODE, STATUS_DETAIL_CODE="S234"
            )  # 全員完了後のステータスコードを設定
        else:
            print("Some users are still not finished with their roles.")
