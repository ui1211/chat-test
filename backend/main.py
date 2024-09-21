# %%


from fastapi import APIRouter, FastAPI, Query, WebSocket
from fastapi.routing import APIRouter
from src.manager import ConnectionManager
from src.room_handlers import RoomManager

# FastAPI用のエンドポイントを定義
app = FastAPI()
router = APIRouter()
manager = ConnectionManager()
room_manager = RoomManager(manager)


@router.websocket("/ws/create/")
async def websocket_create_room(websocket: WebSocket, USER_NAME: str = Query("")):
    """WebSocketでルームを作成"""
    await room_manager.create_room(websocket, USER_NAME)


@router.websocket("/ws/join/")
async def websocket_join_room(websocket: WebSocket, ROOM_CODE: str = Query("0"), USER_NAME: str = Query("")):
    """ルーム参加のWebSocketエンドポイント"""
    await room_manager.join_room(websocket, ROOM_CODE, USER_NAME)


app.include_router(router)
