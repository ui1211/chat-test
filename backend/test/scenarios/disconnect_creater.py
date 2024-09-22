# ルーム作者が退出ボタンを押下した場合のシナリオ

disconnect_creater_scenario = {
    0: {
        "user_name": "fagi",
        "uri": "ws://127.0.0.1:8000/ws/create/?USER_NAME=fagi",
        "command": {},
        "request_status_code": "S221",
        "wait_time": 0,
        "command_sended": False,
        "response_displayed": False,
    },
    1: {
        "user_name": "ui",
        "uri": "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=ui",
        "command": {},
        "request_status_code": "S222",
        "wait_time": 0,
        "command_sended": False,
        "response_displayed": False,
    },
    2: {
        "user_name": "198",
        "uri": "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=198",
        "command": {},
        "request_status_code": "S222",
        "wait_time": 0,
        "command_sended": False,
        "response_displayed": False,
    },
    3: {
        "user_name": "fagi",
        "uri": "",
        "command": {"EVENT": "END_BUTTON"},
        "request_status_code": "S237",
        "wait_time": 0,
        "command_sended": False,
        "response_displayed": False,
    },
    4: {
        "user_name": "ui",
        "uri": "",
        "command": {},
        "request_status_code": "S237",
        "wait_time": 0,
        "command_sended": False,
        "response_displayed": False,
    },
}
