from fastapi import APIRouter, FastAPI, Query, WebSocket, WebSocketDisconnect
from src.button_handlers import ButtonHandlerClass
from src.constants import ALLOWED_COMMANDS
from src.data_store import rooms
from src.helpers import current_time
from src.role_handlers import roleActionClass


class CommunicationClass:

    def __init__(self, manager):
        self.manager = manager
        self.role_action = roleActionClass(self.manager)
        self.button_action = ButtonHandlerClass(self.manager)

    def selective_recursive_update(self, orig_dict, update_dict):
        """辞書を再帰的に更新し、変更があった場合 True とステータスコードを返す"""
        updated = False
        status_code = None

        for key, value in update_dict.items():
            if key in ALLOWED_COMMANDS:
                print(current_time(), "selective_recursive_update", key, value)
                if isinstance(value, dict) and isinstance(orig_dict.get(key), dict):
                    # 再帰的にネストされた辞書も更新する
                    recursive_update, recursive_status = self.selective_recursive_update(orig_dict[key], value)
                    if recursive_update:
                        updated = True
                        status_code = recursive_status or status_code
                else:
                    # 許可されたキーに基づき値を更新
                    if orig_dict.get(key) != value:
                        orig_dict[key] = value
                        updated = True
                        status_code = ALLOWED_COMMANDS[key]  # 対応するステータスコードを設定
            else:
                print(current_time(), "Ignoring unallowed key:", key)

        return updated, status_code

    async def handle_update_command(self, websocket, message_data, ROOM_CODE: str, USER_ID: str):
        """更新コマンドの処理と通知"""
        update_data = message_data.get("UPDATE")
        if update_data:
            if "ROLE" in update_data:
                await self.role_action.role_action_process(update_data["ROLE"], ROOM_CODE, USER_ID)
            else:
                updated, status_code = self.selective_recursive_update(rooms[ROOM_CODE], update_data)

                if updated:
                    await self.manager.send_room_update(ROOM_CODE, status_code)
        else:
            await self.manager.send_error_message(
                websocket,
                status_code="S100",
                status_detail_code="S000",
                message_code="M000",
            )

    async def handle_event(self, websocket: WebSocket, message_data, ROOM_CODE: int, USER_NAME: str, USER_ID: int):
        """イベントを処理"""
        event_type = message_data["EVENT"]

        if event_type == "OMAKASE_BUTTON":
            await self.button_action.process_omakase_button(ROOM_CODE)
        elif event_type == "START_BUTTON":
            await self.button_action.process_start_button(websocket, ROOM_CODE)
        elif event_type == "END_BUTTON":
            pass
            # await process_end_button(USER_NAME, ROOM_CODE, USER_ID)
        elif event_type == "EXIT_BUTTON":
            await self.button_action.process_exit_button(ROOM_CODE, USER_NAME, USER_ID)
        else:
            print(f"Unknown event type: {event_type}")

    def handle_vote_command(self, message_data, ROOM_CODE, USER_ID):
        pass
