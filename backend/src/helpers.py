import json
from datetime import datetime


def current_time():
    """現在時刻をマイクロ秒を削除して返す"""
    return datetime.now().replace(microsecond=0).isoformat()


def ppprint(header, response):
    """JSONデータを整形して表示"""
    if response:  # 空でないことを確認
        res = json.dumps(json.loads(response), indent=4, ensure_ascii=False)
        print(current_time(), header, "\n", res, "\n")
    else:
        print(current_time(), header, "\n", "Empty response\n")
