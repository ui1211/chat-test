# ルーム情報のテンプレート
ROOM_TEMPLATE = {
    # "STATUS": {
    #     "STATUS_CODE": "",
    #     "MESSAGE_CODE": "",
    #     "MESSAGE_TEXT": "",
    # },
    "ROOM": {
        "ROOM_CODE": None,
        "ROOM_NAME": "ワンナイト人狼",
        "ROOM_DISCUSSION_TIME": "180",
        "ROOM_STATUS": "R001",
        "ROOM_USER": {},
        "ROOM_ROLE": [None, None],
        "VOTED_USER_LIST": [],
        "ROOM_DATETIMES": {
            "CREATED_AT": None,
            "START_R001_AT": None,
            "START_R002_AT": None,
            "START_R003_AT": None,
            "START_R004_AT": None,
            "START_R005_AT": None,
            "START_R006_AT": None,
            "START_R007_AT": None,
        },
    },
    "ROLE": {
        "FORTUNE_TELL": None,
        "THIEF": None,
        "ROLE_LIST": {},
    },
    "RESULT": {
        "RESULT_TEXT": "",
        "VOTE_RESULT": {},
        "VICTORY_USER_ID": [],
    },
    "USERS": {},  # 参加している全ユーザの情報
    "USER": {},  # フロントのユーザ情報(接続中のユーザー)
}

# ユーザ情報のテンプレート
USER_TEMPLATE = {
    "USER_ID": None,
    "USER_NAME": None,
    "USER_NUM": None,
    "ROLE_ID": None,
    "ROLE_NAME": None,
    "ROOM_CREATOR": False,
    "VISIBLE_LIST": [],
    "USER_VOTE": None,
    "JOINED_AT": None,
}
