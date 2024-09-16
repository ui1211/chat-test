DEBUG = True

countdown_role_confirmation = 0  # 役職確認画面待機秒数
countdown_role_execution = 0  # 役職実行画面待機秒数


messages = {
    "M000": "メッセージなし",
    "M001": "プレイヤー名を入力してください",
    "M002": "プレイヤー名、ルームコードの両方を入力してください",
    "M004": "ルームコードが誤っています",
    "M005": "役職の数とプレイ人数を統一してください",
    "M011": "プレイヤー名が重複しています",
    "M101": "開始までお待ちください",
    "M102": "占い先を指定してください",
    "M103": "怪盗先を指定してください",
}


# 役職一覧
roles_dict = {
    "20": "村人",
    "21": "人狼",
    "22": "占い師",
    "23": "怪盗",
    "877": "バナナ",  # バナナ
}

#
ALLOWED_COMMANDS = {
    "ROOM": "S210",
    "ROOM_DISCUSSION_TIME": "S211",
    "ROOM_ROLE": "S212",
    "ROLE": "240",
    "FORTUNE_TELL": "S241",
    "THIEF": "S242",
}

#
debugs = {
    "ROOM_CODE": "99999",
    "USER_ID": {
        "fagi": "999",
        "ui": "201",
        "198": "202",
        "mira": "203",
        "cookie": "204",
    },
    "ROLE_LIST": {
        "999": {"USER_NAME": "fagi", "USER_ROLE1": "22", "USER_ROLE2": "22", "ROLE_FIN": False},  # 占い師
        "203": {"USER_NAME": "mira", "USER_ROLE1": "23", "USER_ROLE2": "23", "ROLE_FIN": True},  # 怪盗
        "201": {"USER_NAME": "ui", "USER_ROLE1": "21", "USER_ROLE2": "21", "ROLE_FIN": True},  # 人狼
        "202": {"USER_NAME": "198", "USER_ROLE1": "21", "USER_ROLE2": "21", "ROLE_FIN": True},  # 人狼
        "204": {"USER_NAME": "cookie", "USER_ROLE1": "20", "USER_ROLE2": "20", "ROLE_FIN": True},  # 村人
        "100": {"USER_NAME": None, "USER_ROLE1": "20", "USER_ROLE2": "20", "ROLE_FIN": True},  # 村人、村人
    },
    # "ROLE_LIST": {
    #     "999": {"USER_NAME": "fagi", "USER_ROLE1": "23", "USER_ROLE2": "23", "ROLE_FIN": False},  # 怪盗
    #     "203": {"USER_NAME": "mira", "USER_ROLE1": "22", "USER_ROLE2": "22", "ROLE_FIN": True},  # 占い師
    #     "201": {"USER_NAME": "ui", "USER_ROLE1": "21", "USER_ROLE2": "21", "ROLE_FIN": True},  # 人狼
    #     "202": {"USER_NAME": "198", "USER_ROLE1": "21", "USER_ROLE2": "21", "ROLE_FIN": True},  # 人狼
    #     "204": {"USER_NAME": "cookie", "USER_ROLE1": "20", "USER_ROLE2": "20", "ROLE_FIN": True},  # 村人
    #     "100": {"USER_NAME": None, "USER_ROLE1": "20", "USER_ROLE2": "20", "ROLE_FIN": True},  # 村人、村人
    # },
}
