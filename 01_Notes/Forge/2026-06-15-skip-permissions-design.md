# 📋 設計書：AIエージェントのツール自動承認フラグの追加

## 1. 概要
AIエージェント実行時のツール実行確認を自動でスキップ（自動承認）し、対話不要で処理を進めるため、Antigravity CLIの呼び出しオプションに `--dangerously-skip-permissions` を追加します。

## 2. 対象ファイル
- [scratch/agy_chat.py](file:///C:/Users/PC_User/Forge/scratch/agy_chat.py)
- [scratch/run_loop.py](file:///C:/Users/PC_User/Forge/scratch/run_loop.py)

*(注: `scratch/agent_backprop.py` および `scratch/agent_backprop_with_log.py` にはすでに実装済みです。)*

## 3. 具体的な変更内容

### 3.1 [scratch/agy_chat.py](file:///C:/Users/PC_User/Forge/scratch/agy_chat.py)
`cmd` リストに `"--dangerously-skip-permissions"` を追加します。

```python
            # 2. Antigravity CLI (agy) のコマンドライン引数を組み立て
            # 2回目以降は自動的に文脈を引き継ぐフラグを付与（例: --continue）
            cmd = ["agy", "--print", user_input, "--dangerously-skip-permissions"]
            if is_continued:
                cmd.append("--continue")  # 文脈引き継ぎフラグを自動付与
```

### 3.2 [scratch/run_loop.py](file:///C:/Users/PC_User/Forge/scratch/run_loop.py)
`subprocess.run` の引数リストに `"--dangerously-skip-permissions"` を追加します。

```python
    # 2. Antigravity CLI をバックグラウンドで実行し、出力を取得
    # Windows環境の文字化けを防ぐため、encoding='utf-8' を明記
    try:
        process = subprocess.run(
            ["agy", "--print", prompt, "--dangerously-skip-permissions"], # --printオプションを指定して非対話実行
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            check=True
        )
```

## 4. 検証（テスト）項目
1. **[run_loop.py](file:///C:/Users/PC_User/Forge/scratch/run_loop.py) の疎通確認**:
   `python scratch/run_loop.py "hello とだけ出力してください。"` を実行し、ツール実行承認ダイアログが出ずに対話が完了することを確認する。
2. **[agy_chat.py](file:///C:/Users/PC_User/Forge/scratch/agy_chat.py) の動作確認**:
   `python scratch/agy_chat.py` を実行してチャットシェルを起動し、任意のプロンプトを入力してエラーなく実行が完了することを確認する。
