# 設計書: エージェント・ライフサイクル・フック (Agent Lifecycle Hooks)

本ドキュメントでは、エージェントの各ライフサイクルイベント（PreToolUse、PostToolUse、OnLoopStagnation）において、外部スクリプトをフックとして呼び出す仕組み、およびその検証用シミュレーターの設計を定義します。

---

## 1. ディレクトリ構造

プロジェクトルート配下に以下の構成でファイルを配置します。

```text
.agents/
  ├── hooks.json                     # フック定義ファイル
  └── hooks/
      ├── block-destructive-ops.py   # PreToolUse 用: 破壊的コマンドのブロック
      ├── mask-secrets.py            # PostToolUse 用: 認証情報の漏洩防止
      └── break-loop.py              # OnLoopStagnation 用: ループ停滞の検知・遮断
run_simulator.py                     # エージェントシミュレーター実行スクリプト
```

---

## 2. フック定義ファイル (`.agents/hooks.json`)

```json
{
  "safety-gate": {
    "PreToolUse": [
      {
        "name": "prevent-destructive-commands",
        "script": ".agents/hooks/block-destructive-ops.py"
      }
    ],
    "PostToolUse": [
      {
        "name": "mask-credentials",
        "script": ".agents/hooks/mask-secrets.py"
      }
    ],
    "OnLoopStagnation": [
      {
        "name": "handle-stuck-agent",
        "script": ".agents/hooks/break-loop.py"
      }
    ]
  }
}
```

---

## 3. フックスクリプトの I/O 仕様

各フックスクリプトは、**標準入力 (stdin)** から JSON 形式のデータを受け取り、判定結果を **標準出力 (stdout)** へ JSON 形式で出力します。

### 3.1 PreToolUse (ツール実行前)
* **入力 (stdin) スキーマ**:
  ```json
  {
    "agentId": "coder-subagent",
    "toolCall": {
      "name": "execute_bash",
      "args": { "CommandLine": "string" }
    },
    "loopCount": 1
  }
  ```
* **出力 (stdout) スキーマ**:
  * 許可する場合: `{"decision": "allow"}`
  * ブロックする場合: `{"decision": "deny", "reason": "拒否理由の説明"}`

### 3.2 PostToolUse (ツール実行後)
* **入力 (stdin) スキーマ**:
  ```json
  {
    "agentId": "coder-subagent",
    "toolCall": {
      "name": "execute_bash",
      "args": { "CommandLine": "string" }
    },
    "toolOutput": "string",
    "loopCount": 1
  }
  ```
* **出力 (stdout) スキーマ**:
  * 許可する場合: `{"decision": "allow"}`
  * ブロック（警告終了）する場合: `{"decision": "deny", "reason": "拒否理由の説明"}`

### 3.3 OnLoopStagnation (ループ停滞時)
* **入力 (stdin) スキーマ**:
  ```json
  {
    "agentId": "coder-subagent",
    "loopCount": 6,
    "history": [
      "string"
    ]
  }
  ```
* **出力 (stdout) スキーマ**:
  * 許可（継続）する場合: `{"decision": "allow"}`
  * 遮断（強制終了）する場合: `{"decision": "deny", "reason": "拒否理由の説明"}`

---

## 4. シミュレーター制御フロー (`run_simulator.py`)

シミュレーターは、以下のステップで擬似的にエージェントループを動かし、各ライフサイクルで `subprocess` を用いてフックを起動します。

1. **初期化**: `.agents/hooks.json` をロードし、実行対象のフックスクリプトのパスを特定する。
2. **シナリオ1 (PreToolUse 検証)**:
   * 破壊的コマンド（`rm -rf`）を含むツール実行をシミュレート。
   * PreToolUse フックを呼び出し、`decision` が `deny` になることを検証する。
3. **シナリオ2 (PostToolUse 検証)**:
   * ツール実行後に機密情報（`sk-proj-...`）を含む出力をシミュレート。
   * PostToolUse フックを呼び出し、`decision` が `deny` になることを検証する。
4. **シナリオ3 (OnLoopStagnation 検証)**:
   * エージェントが同一のコマンドを3回連続で実行した状態をシミュレート。
   * OnLoopStagnation フックを呼び出し、`decision` が `deny` になることを検証する。

---

## 5. 検証（テスト）方法

以下のコマンドを実行して、3つのシナリオがすべて正常に動作（ブロック、検知、遮断）することを確認します。

```powershell
python run_simulator.py
```

### 期待される出力例:
```text
=== シナリオ1: 破壊的コマンドのブロック検証 (PreToolUse) ===
[Simulator] 擬似ツール呼び出し: {"name": "execute_bash", "args": {"CommandLine": "rm -rf ./tmp"}} を検知しました。
[Simulator] フック 'prevent-destructive-commands' を実行中...
[Hook Result] {"decision": "deny", "reason": "Destructive command pattern 'rm -rf' is not allowed."}
[Simulator] => 成功: 危険なコマンドがブロックされました。

=== シナリオ2: 認証情報の漏洩防止検証 (PostToolUse) ===
[Simulator] 擬似ツール呼び出し: {"name": "execute_bash", "args": {"CommandLine": "echo sk-proj-12345678901234567890"}}
[Simulator] フック 'mask-credentials' を実行中...
[Hook Result] {"decision": "deny", "reason": "Credential leak prevention: Detected OpenAI API key in tool output."}
[Simulator] => 成功: 機密情報の漏洩が検知され、ブロックされました。

=== シナリオ3: ループ停滞の遮断検証 (OnLoopStagnation) ===
[Simulator] ループ回数: 3, 履歴: ['execute_bash: dir', 'execute_bash: dir', 'execute_bash: dir']
[Simulator] フック 'handle-stuck-agent' を実行中...
[Hook Result] {"decision": "deny", "reason": "Stagnation detected: Agent repeated the action 'execute_bash: dir' 3 times."}
[Simulator] => 成功: ループの停滞が検知され、強制遮断されました。

すべてのシナリオ検証に成功しました！
```
