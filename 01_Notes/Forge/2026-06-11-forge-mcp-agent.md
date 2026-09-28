# Forge MCP Agent & Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Forge側の簡易MCPサーバー（`forge_mcp_agent.py`）を実装し、Antigravity側の接続設定（`.antigravity/agents.json`）を配置する。

**Architecture:** 
- `http.server.BaseHTTPRequestHandler` を使用した軽量なHTTP POSTリスナーを構築し、受信したJSONからパラメータを抽出してシミュレーション関数を実行。結果をJSON形式でレスポンスとして返す。
- 設定ファイル `.antigravity/agents.json` にサブエージェントの設定（エンドポイント、capabilities、id等）を書き込む。

**Tech Stack:** Python 3 (標準ライブラリ `json`, `http.server`, `unittest`), JSON

---

### Task 1: Forge MCPサーバーロジックの実装（TDD）

**Files:**
- Create: `C:\Users\PC_User\Forge\test_forge_mcp.py`
- Create: `C:\Users\PC_User\Forge\forge_mcp_agent.py`

- [ ] **Step 1: テストコード（テストケース）を作成する**
  `C:\Users\PC_User\Forge\test_forge_mcp.py` に以下のテストを作成します。

  ```python
  import unittest
  import json
  # 意図的に未実装のモジュールからインポートして失敗させる
  try:
      from forge_mcp_agent import forge_simulation_skill
  except ImportError:
      forge_simulation_skill = None

  class TestForgeMCP(unittest.TestCase):
      def test_simulation_skill_default(self):
          if forge_simulation_skill is None:
              self.fail("forge_simulation_skill is not imported")
          params = {}
          result = forge_simulation_skill(params)
          self.assertEqual(result["computed_result"], 155.0)
          self.assertEqual(result["status"], "success")
          self.assertEqual(result["agent"], "Forge-Specialist-Agent")

      def test_simulation_skill_custom(self):
          if forge_simulation_skill is None:
              self.fail("forge_simulation_skill is not imported")
          params = {"value": 200}
          result = forge_simulation_skill(params)
          self.assertEqual(result["computed_result"], 310.0)

  if __name__ == "__main__":
      unittest.main()
  ```

- [ ] **Step 2: テストを実行し、インポートエラーで失敗することを確認する**
  Run: `python C:\Users\PC_User\Forge\test_forge_mcp.py`
  Expected: FAIL (ImportError or "forge_simulation_skill is not imported")

- [ ] **Step 3: `forge_mcp_agent.py` のコードを実装する**
  `C:\Users\PC_User\Forge\forge_mcp_agent.py` を以下の内容で作成します。

  ```python
  import json
  from http.server import BaseHTTPRequestHandler, HTTPServer


  # Forgeエージェントのメインロジック（専門スキル）
  def forge_simulation_skill(params):
      # ここにForge側で作り込んだ高度な処理やシミュレーションを記述
      base_value = params.get("value", 100)
      result = base_value * 1.55  # 例: Forge特有の補正ロジック

      return {
          "status": "success",
          "agent": "Forge-Specialist-Agent",
          "computed_result": result,
          "message": "Forge側での高度な演算が完了しました。",
      }


  # Antigravityと通信するための簡易MCPハンドラー
  class ForgeMCPHandler(BaseHTTPRequestHandler):

      def do_POST(self):
          if self.path == "/mcp":
              content_length = int(self.headers["Content-Length"])
              post_data = self.rfile.read(content_length)
              req_json = json.loads(post_data.decode("utf-8"))

              # Antigravityからの指示（タスク）を解析
              print(f"📥 Antigravityからのタスクを受信: {req_json}")
              params = req_json.get("params", {})

              # Forgeのスキルを実行
              response_data = forge_simulation_skill(params)

              # レスポンスを返却
              self.send_response(200)
              self.send_header("Content-Type", "application/json")
              self.end_headers()
              self.wfile.write(json.dumps(response_data).encode("utf-8"))
          else:
              self.send_response(404)
              self.end_headers()


  def run_forge_server(port=8080):
      server = HTTPServer(("localhost", port), ForgeMCPHandler)
      print(f"🚀 Forgeサブエージェントが localhost:{port}/mcp で待機中...")
      server.serve_forever()


  if __name__ == "__main__":
      run_forge_server()
  ```

- [ ] **Step 4: テストを再実行し、すべて PASS することを確認する**
  Run: `python C:\Users\PC_User\Forge\test_forge_mcp.py`
  Expected: OK (2 tests passed)

---

### Task 2: Antigravity設定ファイルの配置

**Files:**
- Create: `C:\Users\PC_User\Forge\.antigravity\agents.json`

- [ ] **Step 1: 設定ファイルを配置する**
  `C:\Users\PC_User\Forge\.antigravity\agents.json` に以下のJSONを書き込みます。

  ```json
  {
    "sub_agents": [
      {
        "id": "forge-specialist",
        "name": "Forgeシミュレーター",
        "type": "mcp_worker",
        "endpoint": "http://localhost:8080/mcp",
        "description": "Forge側で構築された、高度な数値計算とシミュレーションを専門とするサブエージェント",
        "capabilities": ["simulation_execution", "data_patch"],
        "meta": {
          "vibe_mode_compatible": true
        }
      }
    ]
  }
  ```

- [ ] **Step 2: JSON構文の検証を行う**
  Run (PowerShell):
  ```powershell
  Get-Content "C:\Users\PC_User\Forge\.antigravity\agents.json" -Raw | ConvertFrom-Json
  ```
  Expected: JSONパースエラーなしで、パースされたオブジェクトが出力されること。
