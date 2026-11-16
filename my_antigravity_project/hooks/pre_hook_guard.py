# pre_hook_guard.py の例
import re
import sys

def check_payload(content):
    # APIキーや秘密情報のパターンマッチ
    if re.search(r"sk-[a-zA-Z0-9]{20,}", content):
        print("Error: API Key detected in prompt!", file=sys.stderr)
        sys.exit(1) # ブロック

if __name__ == "__main__":
    # 入力内容の検査処理
    pass
