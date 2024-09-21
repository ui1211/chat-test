from src.data_store import rooms
from src.helpers import current_time


class voteManagerClass:

    def __init__(self, manager):
        self.manager = manager

    async def handle_vote_command(self, message_data: dict, ROOM_CODE: int, USER_ID: int):
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
            await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S251")

            print(current_time(), f"User {USER_ID} voted for {vote_target_id}")

            # 全員の投票が完了したかを確認
            all_users_voted = self.check_if_all_users_voted(ROOM_CODE)
            if all_users_voted:
                print(current_time(), f"All users in room {ROOM_CODE} have voted.")
                await self.proceed_to_next_phase(ROOM_CODE)
                await self.determine_victory(ROOM_CODE)
            else:
                print(current_time(), f"Waiting for more users to vote in room {ROOM_CODE}.")
        else:
            print(f"Invalid vote data: {message_data}")

    def check_if_all_users_voted(self, ROOM_CODE: int) -> bool:
        """全ユーザーが投票を完了したかチェック"""
        room_data = rooms[ROOM_CODE]
        total_users = len(room_data["USERS"])
        voted_users = len(room_data["ROOM"]["VOTED_USER_LIST"])

        # 全ユーザーが投票した場合にTrueを返す
        return voted_users >= total_users

    async def proceed_to_next_phase(self, ROOM_CODE: int):
        """全員の投票が完了したら次のフェーズに進む処理"""
        # 投票結果の集計などを行うフェーズ
        print(current_time(), f"Proceeding to the next phase in room {ROOM_CODE}...")

        # 例: 結果発表フェーズへ移行
        rooms[ROOM_CODE]["ROOM"]["ROOM_STATUS"] = "R007"  # 結果発表画面
        await self.manager.send_room_update(ROOM_CODE, STATUS_DETAIL_CODE="S252")

    async def determine_victory(self, ROOM_CODE: int):
        """勝利条件の判定"""
        room_data = rooms[ROOM_CODE]
        role_list = room_data["ROLE"]["ROLE_LIST"]

        # 人狼陣営と村人陣営のプレイヤーを取得
        werewolves = [user_id for user_id, role_data in role_list.items() if role_data["USER_ROLE1"] == "21"]
        villagers = [user_id for user_id, role_data in role_list.items() if role_data["USER_ROLE1"] == "20"]

        # 投票結果から処刑されたユーザーを取得
        voted_out_user_id = await self.get_voted_out_user(ROOM_CODE)

        # 投票の集計結果を取得
        vote_results = await self.get_vote_results(ROOM_CODE)
        max_vote_count = max(len(votes) for votes in vote_results.values())
        max_voted_users = [user_id for user_id, votes in vote_results.items() if len(votes) == max_vote_count]

        # 初期化: 陣営とユーザIDリストをRESULTに追加
        room_data["RESULT"]["RESULT_TEXT"] = ""
        room_data["RESULT"]["VOTE_RESULT"] = vote_results
        room_data["RESULT"]["USER_ID_LIST"] = []

        # 1. 投票数の一番多い人が人狼陣営の場合 → 村人陣営の勝利
        if any(user_id in werewolves for user_id in max_voted_users):
            print(current_time(), f"Room {ROOM_CODE}: 村人陣営の勝利 (人狼が投票で選ばれたため)")
            room_data["ROOM"]["VICTORY"] = "villager"
            room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
            room_data["RESULT"]["USER_ID_LIST"] = villagers
        # 2. 投票数の一番多い人が村人陣営で、村内に人狼が1人以上いる場合 → 人狼陣営の勝利
        elif len(max_voted_users) == 1 and max_voted_users[0] in villagers and len(werewolves) > 0:
            print(current_time(), f"Room {ROOM_CODE}: 人狼陣営の勝利 (村人が処刑され、村内に人狼がいるため)")
            room_data["ROOM"]["VICTORY"] = "werewolf"
            room_data["RESULT"]["RESULT_TEXT"] = "人狼陣営の勝利"
            room_data["RESULT"]["USER_ID_LIST"] = werewolves
        # 3. 投票数の一番多い人が村人陣営で、村内に人狼がいない場合 → 村人陣営の勝利
        elif len(max_voted_users) == 1 and max_voted_users[0] in villagers and len(werewolves) == 0:
            print(current_time(), f"Room {ROOM_CODE}: 村人陣営の勝利 (人狼がいないため)")
            room_data["ROOM"]["VICTORY"] = "villager"
            room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
            room_data["RESULT"]["USER_ID_LIST"] = villagers
        # 4. 全員が一票ずつで、人狼陣営がいない場合 → 平和村
        elif len(max_voted_users) == len(role_list) and len(werewolves) == 0:
            print(current_time(), f"Room {ROOM_CODE}: 平和村 (全員が一票ずつかつ人狼がいない)")
            room_data["ROOM"]["VICTORY"] = "peace"
            room_data["RESULT"]["RESULT_TEXT"] = "平和村"
            room_data["RESULT"]["USER_ID_LIST"] = list(role_list.keys())  # 全員が平和村の一員
        # 5. 全員が一票ずつで、人狼陣営がいる場合 → 人狼陣営の勝利
        elif len(max_voted_users) == len(role_list) and len(werewolves) > 0:
            print(current_time(), f"Room {ROOM_CODE}: 人狼陣営の勝利 (全員が一票ずつかつ人狼がいるため)")
            room_data["ROOM"]["VICTORY"] = "werewolf"
            room_data["RESULT"]["RESULT_TEXT"] = "人狼陣営の勝利"
            room_data["RESULT"]["USER_ID_LIST"] = werewolves
        else:
            # 予期しない状況に対するデフォルトの村人陣営勝利
            print(current_time(), f"Room {ROOM_CODE}: 村人陣営の勝利 (デフォルト)")
            room_data["ROOM"]["VICTORY"] = "villager"
            room_data["RESULT"]["RESULT_TEXT"] = "村人陣営の勝利"
            room_data["RESULT"]["USER_ID_LIST"] = villagers

        # 投票結果をVOTE_RESULTに記載
        print(current_time(), f"Vote results: {vote_results}")

        await self.manager.send_room_update(ROOM_CODE, "S261", "M030")

    async def get_voted_out_user(self, ROOM_CODE: int):
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
            print(current_time(), f"User {voted_out_user_id} has been voted out.")
            return voted_out_user_id
        return None

    async def get_vote_results(self, ROOM_CODE: int) -> dict:
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

    def check_thief_victory(self, user_id: int, room_data: dict) -> bool:
        """怪盗の勝利条件を判定する関数"""
        # 実装例：怪盗が盗んだ役職によって勝利条件を判定
        thief_role = room_data["ROLE"]["ROLE_LIST"][user_id]["USER_ROLE2"]  # 怪盗が盗んだ役職
        if thief_role == "21":  # 例: 怪盗が人狼になった場合、人狼陣営に勝利を移す
            return True
        return False
