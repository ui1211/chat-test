# コマンドリスト
creater_commands = {
    "cmd1": {
        "cmd": {"UPDATE": {"ROOM": {"ROOM_DISCUSSION_TIME": 999}}},  # 送信するコマンド
        "res": "S211",  # 想定されるレスポンス
        "send": False,  # コマンド送信したかどうか
        "display": False,  # テストケースで一度表示したか判定するフラグ
    },
    "cmd2": {
        "cmd": {"UPDATE": {"ROOM": {"ROOM_ROLE": [20, 20, 21, 22, None, None, None]}}},
        "res": "S212",
        "send": False,
        "display": False,
    },
    "cmd3": {
        "cmd": {"EVENT": "OMAKASE_BUTTON"},
        "res": "S231",
        "send": False,
        "display": False,
    },
    "cmd4": {
        "cmd": {"EVENT": "START_BUTTON"},
        "res": "S232",
        "send": False,
        "display": False,
    },
    "cmd5": {
        "cmd": {},  # スタートボタン押下後にカウントダウン終了時のメッセージを受け取る
        "res": "S233",
        "send": False,
        "display": False,
    },
    "cmd6": {  # 占い師コマンド
        "cmd": {"UPDATE": {"ROLE": {"FORTUNE_TELL": 100}}},
        "res": "S243",
        "send": False,
        "display": False,
    },
    # "cmd7": {  # 怪盗コマンド
    #     "cmd": {},  # {"UPDATE": {"ROLE": {"THIEF": 201}}},
    #     "res": "S244",
    #     "send": False,
    #     "display": False,
    # },
    "cmd8": {  # すべての役職処理が完了
        "cmd": {},
        "res": "S234",
        "send": False,
        "display": False,
    },
    # "cmd9": {  # 役職実行画面で指定時間が経過
    #     "cmd": {},
    #     "res": "S235",
    #     "send": False,
    #     "display": False,
    # },
    "cmd10": {  # ユーザに投票
        "cmd": {"VOTE": {"USER_ID": 201}},
        "res": "S251",
        "send": False,
        "display": False,
    },
    # "cmd10-2": {  # ユーザに投票(投票先を変更/更新)
    #     "cmd": {"VOTE": {"USER_ID": 202}},
    #     "res": "S251",
    #     "send": False,
    #     "display": False,
    # },
    "cmd11": {  # すべてのユーザの投票が完了
        "cmd": {},
        "res": "S252",
        "send": False,
        "display": False,
    },
    "cmd12": {  # 投票結果
        "cmd": {},
        "res": "S261",
        "send": False,
        "display": False,
    },
}


# joiner 用のユーザーごとのコマンドリスト
joiner_commands_by_user = {
    "ui": {
        "cmd1": {  # 投票
            "cmd": {"VOTE": {"USER_ID": 201}},
            "res": "S251",
            "send": False,
            "display": False,
        },
    },
    "198": {
        "cmd1": {  # 投票
            "cmd": {"VOTE": {"USER_ID": 202}},
            "res": "S251",
            "send": False,
            "display": False,
        },
    },
    "mira": {
        "cmd7": {  # 怪盗コマンド
            "cmd": {"UPDATE": {"ROLE": {"THIEF": 201}}},
            "res": "S244",
            "send": False,
            "display": False,
        },
        "cmd1": {  # 投票
            "cmd": {"VOTE": {"USER_ID": 203}},
            "res": "S251",
            "send": False,
            "display": False,
        },
    },
    "cookie": {
        "cmd2": {  # 退出ボタン
            "cmd": {"EVENT": "EXIT_BUTTON"},
            "res": "S236",
            "send": False,
            "display": False,
        },
        "cmd1": {  # 投票
            "cmd": {"VOTE": {"USER_ID": 201}},
            "res": "S251",
            "send": False,
            "display": False,
        },
    },
}

normal_play_scenario_commands = {
    1: {
        "user_name": "fagi",
        "command": "",
        "request_statsu_code": "",
        "wait_time": "",
        "command_sended": "",
        "response_dipslayed": "",
    },
    2: {
        "user_name": "fagi",
        "command": "",
        "request_statsu_code": "",
        "wait_time": "",
        "command_sended": "",
        "response_dipslayed": "",
    },
}
