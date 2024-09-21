# %%

from data_store import rooms
from manager import ConnectionManager


class ButtonHandlerClass:
    """
    ボタン操作に関するクラス
    """

    def __init__(self):
        self.manager = ConnectionManager()

    async def process_omakase_button(self, ROOM_CODE: str, rooms: dict):
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

    def process_start_button(self):
        pass

    def process_end_button(self):
        pass

    def process_exit_button(self):
        pass

    # if event_type == "OMAKASE_BUTTON":
    #     await process_omakase_button(ROOM_CODE)
    # elif event_type == "START_BUTTON":
    #     await process_start_button(websocket, ROOM_CODE)
    # elif event_type == "END_BUTTON":
    #     await process_end_button(USER_NAME, ROOM_CODE, USER_ID)
    # elif event_type == "EXIT_BUTTON":
    #     await process_exit_button(USER_NAME, ROOM_CODE, USER_ID)


if __name__ == "__main__":
    buttun_handler = ButtonHandlerClass()

    buttun_handler.process_omakase_button(ROOM_CODE="99999")
