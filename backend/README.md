# 接続

```bash
uvicorn OneNightWerewolf:app --reload
```

##　ルーム作成
```bash
wscat -c "ws://127.0.0.1:8000/ws/create/?USER_NAME=Alice"
```

## ルーム参加
```bash
wscat -c "ws://127.0.0.1:8000/ws/join/?ROOM_CODE=999999&USER_NAME=Bob"
```

# 接続後

## 配役変更(例)
```python
{"UPDATE": {"ROOM": {"ROOM_ROLE": [20,20,21,22]}}}
```
## 開始ボタン
```python
{"EVENT": "START_BUTTON"}
```

