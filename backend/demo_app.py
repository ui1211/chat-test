import asyncio
import json

import streamlit as st
import websockets


class RealTimeChatApp:
    def __init__(self):
        self.user_name = ""
        self.room_code = ""
        self.join_type = ""
        self.uri = ""

    def main(self):
        if "room_status" not in st.session_state:
            self.layout()
        else:
            if st.session_state["room_status"] == "create":
                self.create_room()

    def start_view(self):

        @st.dialog("プレイヤー名を入力してください")
        def create_modal():
            user_name = st.text_input(label="user_name", value="")
            st.session_state["room_status"] = "create"

            if st.button("決定"):
                uri = f"ws://127.0.0.1:8000/ws/create/{user_name}"
                asyncio.run(self.websocket_handler(uri))
                st.session_state["user_name"] = user_name
                st.rerun()

        if st.button("作成"):
            create_modal()

        if st.button("参加"):
            pass

        if st.button("観戦"):
            pass

    def create_room(self):
        st.write("create_room")

    def layout(self):

        self.start_view()

    # def layout_login(self):
    #     st.title("リアルタイムチャット")
    #     self.user_name = st.text_input("ユーザー名を入力してください:")
    #     self.room_code = st.text_input("ルームコードを入力してください:")
    #     self.join_type = st.radio("参加タイプを選択してください", ("作成", "参加"))

    #     if st.button("接続"):
    #         if self.join_type == "作成":
    #             self.uri = f"ws://127.0.0.1:8000/ws/create/{self.user_name}"
    #         elif self.join_type == "参加":
    #             self.uri = f"ws://127.0.0.1:8000/ws/join/{self.room_code}/{self.user_name}"

    #         st.session_state.page = "chat"
    #         st.rerun()

    # def layout_chat(self):
    #     st.title("チャットルーム")
    #     st.write(f"ルームコード: {self.room_code}, ユーザー名: {self.user_name}")

    #     if "connected" not in st.session_state:
    #         st.session_state.connected = False

    #     if st.button("切断"):
    #         st.session_state.connected = False
    #         st.session_state.page = "login"
    #         st.rerun()

    #     if not st.session_state.connected:
    #         asyncio.run(self.websocket_handler(self.uri))

    async def websocket_handler(self, uri):
        async with websockets.connect(uri) as websocket:
            st.session_state.connected = True
            if self.join_type == "作成":
                await websocket.send(json.dumps({"type": "create", "user_name": self.user_name}))
            else:
                await websocket.send(json.dumps({"type": "join", "user_name": self.user_name}))

            st.write(f"Connected to room {self.room_code} as {self.user_name}")

            async def receive_message():
                while st.session_state.connected:
                    message = await websocket.recv()
                    st.write(f"受信: {message}")

            async def send_message():
                while st.session_state.connected:
                    message = st.text_input("メッセージを入力してください:", key="message_input")
                    if st.button("送信"):
                        await websocket.send(json.dumps({"message": message, "user_name": self.user_name}))

            await asyncio.gather(receive_message(), send_message())


if __name__ == "__main__":
    app = RealTimeChatApp()
    app.main()
