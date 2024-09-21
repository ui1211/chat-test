# 接続

```bash
uvicorn OneNightWerewolf:app --reload
uvicorn main:app --reload
```

```
curl "http://127.0.0.1:8000/manage/"
```

##　ルーム作成
```bash
wscat -c "ws://127.0.0.1:8000/ws/create/?USER_NAME=fagi"
```

## ルーム参加
```bash
wscat -c "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=ui"
wscat -c "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=198"
wscat -c "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=mira"
wscat -c "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=99999&USER_NAME=cookie"
```

# 接続後
## ルーム作成画面処理
```python
# 議論時間変更
{"UPDATE": {"ROOM": {"ROOM_DISCUSSION_TIME": 999}}}

# 配役変更
{"UPDATE": {"ROOM": {"ROOM_ROLE": [20,20,21,22]}}}
# お任せボタン
{"EVENT": "OMAKASE_BUTTON"}
#
```
## 開始ボタン
```python
{"EVENT": "START_BUTTON"}
```

