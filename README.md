# chat-test

## FastAPIの通信テスト

backend側　サーバ起動
```bash
uvicorn easy_test:app --reload
```

httpリスエストテスト
```bash
#ルームNoとユーザ名の生成
curl http://127.0.0.1:8000/create_room?user_name=test

#ルームNoが存在するかチェックし、所属しているプレイヤーを表示
curl http://127.0.0.1:8000/check_room?room_number=5329
```



## Vueとpython(FastAPI)のwebscoket連携テスト

ルームチャット機能のサンプル

## フロントエンド
frontend/chat-test/App.vue   
frontend/chat-test/components/Chat.vue   

## バックエンド
backend/main.py   

## デモ画像
![](images/Animation.gif)