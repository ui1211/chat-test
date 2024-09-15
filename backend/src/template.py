# ルーム情報のテンプレート
ROOM_TEMPLATE = {
    "STATUS": {
        "STATUS_CODE": "",
        "MESSAGE_CODE": "",
        "MESSAGE_TEXT": "",
    },
    "ROOM": {
        "ROOM_CODE": None,
        "ROOM_NAME": "ワンナイト人狼",
        "ROOM_DISCUSSION_TIME": "180",
        "ROOM_STATUS": "R001",
        "ROOM_USER": {"100": None},
        "ROOM_ROLE": [None, None],
        "VOTED_USER_LIST": [],
    },
    "ROLE": {
        "FORTUNE_TELL": None,
        "THIEF": None,
        "ROLE_LIST": {},
    },
    "RESULT": {
        "RESULT_TEXT": "",
        "VOTE_RESULT": {},
    },
    "USERS": {},  # 参加している全ユーザの情報
    "USER": {},  # フロントのユーザ情報(接続中のユーザー)
}

# ユーザ情報のテンプレート
USER_TEMPLATE = {
    "USER_ID": None,
    "USER_NAME": None,
    "ROLE_ID": None,
    "ROLE_NAME": None,
    "ROOM_CREATOR": False,
    "VISIBLE_LIST": [],
    "USER_VOTE": None,
}
