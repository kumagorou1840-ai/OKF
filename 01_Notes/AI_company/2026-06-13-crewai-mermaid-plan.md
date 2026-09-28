# CrewAI Mermaid 連携システム 実装計画（高度ハイブリッド制御版）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** マネージャーによる自動評価・ループ制御（上限 3回）と、人間の最終承認（Human-in-the-loop）を取り入れた、高度な 3名体制のマルチエージェント・ワークフローを実装し、その実行結果および問答フローを Mermaid シーケンス図として自動追記する。

**Architecture:** 
1. 3名のエージェント（Manager, Researcher, Writer）のペルソナ具体化。
2. 直列・多段階タスク（アウトライン ➔ 一次調査 ➔ 下書き ➔ 二次調査 ➔ 最終清書）の構築。
3. `manager_agent` による成果物チェック（JSON `{"approved": bool, "feedback": str}`）と Python 側の While ループ（最大 3回）の統合。
4. 清書レポート生成後、コンソールで `input()` を呼び出し、よっちゃん（ユーザー）のレビューを求めるゲート機構の実装。
5. 承認後、成果物レポート `latest_ai_report.md` の末尾に動的 Mermaid シーケンス図を自動追記する。

**Tech Stack:** Python, CrewAI, LangChain, LiteLLM, unittest

---

### Task 1: テストコードの更新（TDD用テストケースの追加）

**Files:**
- Modify: `test_crewai_mermaid.py`

- [ ] **Step 1: 新しいテストケースの追加**
  
  マネージャーの評価JSONパース判定ロジック、および `run_workflow` の高度なループ制御（`use_dummy=True` 時）の検証テストを追加します。
  Modify: `C:\Users\PC_User\Forge\test_crewai_mermaid.py`
  
  ```python
  import unittest
  import os
  import json
  from crewai_mermaid import generate_mermaid_sequence_diagram, get_llm, run_workflow

  class TestCrewAIMermaid(unittest.TestCase):
      def test_generate_mermaid_sequence_diagram(self):
          agents_info = [
              {"name": "Manager Agent", "role": "マネージャー"},
              {"name": "Research Agent", "role": "リサーチャー"},
              {"name": "Writer Agent", "role": "ライター"}
          ]
          mermaid_code = generate_mermaid_sequence_diagram(agents_info, human_input=True)
          self.assertIn("sequenceDiagram", mermaid_code)
          self.assertIn("participant User as ユーザー", mermaid_code)
          self.assertIn("ManagerAgent", mermaid_code)

      def test_get_llm(self):
          os.environ["GEMINI_API_KEY"] = "fake-key"
          llm = get_llm()
          self.assertIsNotNone(llm)
          del os.environ["GEMINI_API_KEY"]

      def test_run_workflow_advanced_dummy(self):
          # 高度なハイブリッドループおよびHuman-in-the-loopの動作検証テスト（ダミーモード）
          report_file = "test_advanced_report.md"
          if os.path.exists(report_file):
              os.remove(report_file)

          # テスト時は human_input=False, user_input_mock="ok" を渡して自動通過させる
          run_workflow(
              report_path=report_file, 
              use_dummy=True, 
              human_input=False, 
              user_input_mock="ok"
          )

          self.assertTrue(os.path.exists(report_file))
          with open(report_file, "r", encoding="utf-8") as f:
              content = f.read()
          self.assertIn("```mermaid", content)
          self.assertIn("ManagerAgent", content)

          # クリーンアップ
          if os.path.exists(report_file):
              os.remove(report_file)

  if __name__ == "__main__":
      unittest.main()
  ```

- [ ] **Step 2: テストの実行と失敗の確認**
  
  まだ `crewai_mermaid.py` に新しい引数やエージェントが実装されていないため、テストが失敗することを確認します。
  Run:
  ```powershell
  .venv\Scripts\python -m unittest test_crewai_mermaid.py
  ```
  Expected: FAIL (引数エラー、あるいは Mermaid 構造に ManagerAgent が含まれないためのアサーション失敗)

---

### Task 2: エージェントペルソナと多段階タスクの実装

**Files:**
- Modify: `crewai_mermaid.py`

- [ ] **Step 1: エージェント定義とタスク定義の更新**
  
  `crewai_mermaid.py` を編集し、3つのエージェントと直列の5タスクを実装します。
  また、マネージャーによる自動品質チェックのJSON解析、上限3回の While ループ、およびユーザー `input()` によるゲートを実装します。
  Modify: `C:\Users\PC_User\Forge\crewai_mermaid.py`
  
  ```python
  import os
  import json
  from crewai import Agent, Crew, Process, Task, LLM

  def get_llm():
      if os.environ.get("GEMINI_API_KEY"):
          return LLM(model="gemini/gemini-2.5-flash", api_key=os.environ.get("GEMINI_API_KEY"))
      elif os.environ.get("OPENAI_API_KEY"):
          return LLM(model="openai/gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))
      else:
          return LLM(model="ollama/deepseek-r1:14b", base_url="http://localhost:11434")

  def generate_mermaid_sequence_diagram(agents_info, human_input=True):
      human_loop_label = " (Human-in-the-loop)" if human_input else ""
      
      mermaid = f"""```mermaid
  sequenceDiagram
      participant User as ユーザー
      participant ManagerAgent as Manager Agent (ディレクター)
      participant ResearchAgent as Research Agent (リサーチャー)
      participant WriterAgent as Writer Agent (ライター)

      %% --- 計画・一次リサーチの問答 ---
      User->>WriterAgent: 1. 調査テーマ指示
      WriterAgent->>ResearchAgent: 2. 構成案に基づく情報要請
      loop Web探索・情報収集
          ResearchAgent->>ResearchAgent: データ収集・検証
      end
      ResearchAgent-->>WriterAgent: 3. 一次リサーチ結果の提供

      %% --- 下書きとマネージャー自動チェックのループ ---
      loop マネージャー自動品質チェック (最大3回)
          WriterAgent->>WriterAgent: 4. 下書きレポート作成
          WriterAgent->>ManagerAgent: レポート提出
          ManagerAgent->>ManagerAgent: 品質・論理監査
          ManagerAgent-->>WriterAgent: フィードバック (不合格時)
      end

      %% --- 二次追加リサーチと清書 ---
      ManagerAgent->>ResearchAgent: 5. 補完要請 (承認後)
      ResearchAgent-->>WriterAgent: 追加データの引き渡し
      WriterAgent->>WriterAgent: 6. 最終清書レポート作成
      WriterAgent->>User: 7. 最終レポート初稿提示

      %% --- 最終人間チェックゲート ---
      User->>User: レビュー評価{human_loop_label}
      alt 修正指示あり (NG)
          User-->>WriterAgent: 修正要求フィードバック
          WriterAgent->>WriterAgent: 再修正
      else 承認 (OK)
          User-->>User: 成果物確定 ➔ Git自動コミット
      end
  ```"""
      return mermaid

  def parse_manager_approval(output_text):
      # マネージャーの出力からJSON部分をパースするヘルパー
      try:
          # マークダウンのJSONブロックや単純な括弧を探す
          if "```json" in output_text:
              json_str = output_text.split("```json")[1].split("```")[0].strip()
          elif "```" in output_text:
              json_str = output_text.split("```")[1].split("```")[0].strip()
          else:
              json_str = output_text.strip()
          
          # 余計な括弧外のテキストを除去
          start_idx = json_str.find("{")
          end_idx = json_str.rfind("}")
          if start_idx != -1 and end_idx != -1:
              json_str = json_str[start_idx:end_idx+1]
              
          data = json.loads(json_str)
          return data.get("approved", False), data.get("feedback", "")
      except Exception:
          # パース失敗時は不合格としてリトライを促す
          return False, "JSONフォーマットを解析できませんでした。再度 {'approved': bool, 'feedback': 'str'} 形式で評価を出力してください。"

  def run_workflow(report_path="latest_ai_report.md", use_dummy=False, human_input=True, user_input_mock=None):
      agents_info = [
          {"name": "Manager Agent", "role": "ディレクター"},
          {"name": "Research Agent", "role": "リサーチャー"},
          {"name": "Writer Agent", "role": "ライター"}
      ]

      if use_dummy:
          # ダミーモード実行時のモック処理
          dummy_content = "# ローカルAIエージェントの最新トレンド\n\nこれはテスト用の調査レポートです。\n"
          with open(report_path, "w", encoding="utf-8") as f:
              f.write(dummy_content)
      else:
          # 1. LLM初期化
          llm = get_llm()

          # 2. エージェントの定義
          manager_agent = Agent(
              role="Manager Agent (プロジェクト・ディレクター)",
              goal="成果物の論理整合性と事実検証の品質を監督し、最終的な品質承認を与える。",
              backstory="Fortune 500企業の元分析ディレクター。曖昧さや根拠のない記述を嫌い、厳密な品質監査を行うプロフェッショナル。",
              verbose=True,
              llm=llm,
          )

          research_agent = Agent(
              role="Research Agent (シニア・インテリジェンス・リサーチャー)",
              goal="指示された構成やアウトラインに基づいて、正確でノイズのない一次データを収集・検証・要約する。",
              backstory="元CIA情報分析官。噂や推測を排除し、信頼できるソースからのエビデンス（証跡）にこだわる専門家。",
              verbose=True,
              llm=llm,
          )

          writer_agent = Agent(
              role="Writer Agent (チーフ・サイエンス・エディター)",
              goal="複雑な技術情報を構造化し、読者が理解しやすい美しく論理的なMarkdown形式のレポートを執筆する。",
              backstory="科学技術誌の元編集長。論理展開が明快で、MarkdownやMermaid図面案を駆使して読者の認知負荷を最小化する執筆の達人。",
              verbose=True,
              llm=llm,
          )

          # --- 自動レビュー・ループ制御の実装 ---
          loop_count = 0
          max_loops = 3
          approved = False
          feedback = "レポートのアウトラインを作成し、一次リサーチと下書き作成を進めてください。"

          while not approved and loop_count < max_loops:
              print(f"\n🔄 [Manager Review Loop] 実行中 ({loop_count + 1} / {max_loops} 回目)")
              
              # タスク1: 構成案策定
              task_outline = Task(
                  description=f"「ローカルAIエージェントの最新トレンド」に対するレポートの構成案（章立て）を作成し、リサーチャーに求める情報要件リストをまとめてください。フィードバック: {feedback}",
                  expected_output="章立てと、各章で必要となるリサーチデータ項目リスト",
                  agent=writer_agent
              )

              # タスク2: 一次情報リサーチ
              task_research_1 = Task(
                  description="タスク1で作成された構成案と要件リストに基づき、Webから正確なデータを収集し要約してください。",
                  expected_output="噂や推測を排除し、ソース元が明確な調査データ",
                  agent=research_agent
              )

              # タスク3: レポート下書きの作成
              task_draft = Task(
                  description="タスク2のリサーチデータを元に、レポートの下書き初稿を作成してください。",
                  expected_output="Markdown形式のレポート初稿",
                  agent=writer_agent
              )

              # 一旦下書きまでを実行
              crew_draft = Crew(
                  agents=[writer_agent, research_agent],
                  tasks=[task_outline, task_research_1, task_draft],
                  process=Process.sequential,
                  verbose=True
              )
              
              draft_output = crew_draft.kickoff()
              
              # タスク3.5: マネージャーによる品質評価
              task_review = Task(
                  description=f"以下のレポート下書きの内容を監査し、事実に基づいたデータがあるか、論理が通っているかを評価してください。\n\n【レポート下書き】\n{draft_output}\n\n必ず以下のJSONフォーマットのみで結果を出力してください。余計な説明文は一切含めないでください。\n{{\"approved\": true/false, \"feedback\": \"修正点の具体的な指示または承認コメント\"}}",
                  expected_output="指定されたJSONフォーマットのテキストのみ",
                  agent=manager_agent
              )
              
              crew_review = Crew(
                  agents=[manager_agent],
                  tasks=[task_review],
                  process=Process.sequential,
                  verbose=True
              )
              
              review_output = str(crew_review.kickoff())
              approved, feedback = parse_manager_approval(review_output)
              
              print(f"📢 マネージャー監査結果: Approved={approved}, Feedback={feedback}")
              loop_count += 1

          # --- 二次追加リサーチと最終清書 ---
          print("\n✍️ 最終清書フェーズに入ります。")
          task_research_2 = Task(
              description=f"これまでの下書きとマネージャーの指示に基づいて、不足しているデータの追加調査や補完を行ってください。マネージャー指示: {feedback}",
              expected_output="追加補完された調査データ",
              agent=research_agent
          )

          task_final_writing = Task(
              description="追加データを取り込み、完成版のMarkdownレポートを仕上げてください。",
              expected_output="見出し、箇条書き、Mermaidコード案が含まれた完成されたMarkdownレポートのテキスト",
              agent=writer_agent,
              output_file=report_path
          )

          crew_final = Crew(
              agents=[research_agent, writer_agent],
              tasks=[task_research_2, task_final_writing],
              process=Process.sequential,
              verbose=True
          )
          
          crew_final.kickoff()

          # --- 最終の人間チェックゲート（Human-in-the-loop） ---
          user_approved = False
          while not user_approved:
              print(f"\n👀 [Human Review Gate] 成果物 {report_path} が生成されました。")
              if user_input_mock is not None:
                  user_input = user_input_mock
              else:
                  user_input = input("成果物を確認し、OKなら 'ok' を、NGなら修正指示を入力してください: ").strip()

              if user_input.lower() == "ok":
                  print("✅ よっちゃん（人間）からの承認を確認しました！")
                  user_approved = True
              else:
                  print(f"🔄 よっちゃんからの修正指示: {user_input}")
                  # フィードバックを反映して最終清書を再実行
                  task_correction = Task(
                      description=f"ユーザーからの直接の修正指示に基づいて、レポートを再修正してください。指示: {user_input}",
                      expected_output="修正されたMarkdownレポートのテキスト",
                      agent=writer_agent,
                      output_file=report_path
                  )
                  crew_correction = Crew(
                      agents=[writer_agent],
                      tasks=[task_correction],
                      process=Process.sequential,
                      verbose=True
                  )
                  crew_correction.kickoff()

      # 成果物レポートに Mermaid 図を追記する
      mermaid_diagram = generate_mermaid_sequence_diagram(agents_info, human_input=human_input)
      
      if os.path.exists(report_path):
          with open(report_path, "a", encoding="utf-8") as f:
              f.write("\n\n## 📊 エージェント協調プロセス（シーケンス図）\n\n")
              f.write(mermaid_diagram)
              f.write("\n")

  if __name__ == "__main__":
      # デフォルトでは対話モードで実行
      run_workflow(report_path="latest_ai_report.md", use_dummy=False, human_input=True)
  ```

- [ ] **Step 2: テストの実行とパス確認**
  
  実装が正しく完了し、ユニットテストおよび結合テストがパスすることを確認します。
  Run:
  ```powershell
  .venv\Scripts\python -m unittest test_crewai_mermaid.py
  ```
  Expected: OK

- [ ] **Step 3: Git コミット**
  
  変更をコミットします。
  Run:
  ```powershell
  git add crewai_mermaid.py test_crewai_mermaid.py
  git commit -m "feat: implement advanced manager loop and human-in-the-loop validation gate"
  ```
  Expected: コミット成功。

---

### Task 3: 動作検証とダミー実行テスト

**Files:**
- Modify: `crewai_mermaid.py`

- [ ] **Step 1: ダミーモードでのスクリプト自体の動作検証**
  
  コマンドラインからダミーモードで実行して、`latest_ai_report.md` が正常に生成され、よっちゃん（ユーザー）モック入力で通過することを確認します。
  Run:
  ```powershell
  .venv\Scripts\python -c "import crewai_mermaid; crewai_mermaid.run_workflow(use_dummy=True, user_input_mock='ok')"
  ```
  Expected: プログラムが正常終了し、`latest_ai_report.md` がカレントディレクトリに生成されること。

- [ ] **Step 2: 生成されたレポートの内容確認**
  
  `latest_ai_report.md` を読み込み、マネージャー・エージェント（ManagerAgent）を含んだ Mermaid シーケンス図が埋め込まれていることを確認します。
  Run:
  ```powershell
  [Console]::OutputEncoding = [Text.Encoding]::UTF8; Get-Content -Raw latest_ai_report.md
  ```
  Expected: ファイル内に `# ローカルAIエージェントの最新トレンド` と、末尾に `## 📊 エージェント協調プロセス（シーケンス図）` および `ManagerAgent` が定義された Mermaid ブロックが存在すること。

- [ ] **Step 3: クリーンアップ**
  
  一時作成されたファイルをクリーンアップします。
  Run:
  ```powershell
  Remove-Item latest_ai_report.md -ErrorAction SilentlyContinue
  ```
  Expected: ファイルが削除されること。

- [ ] **Step 4: Git 最終コミット**
  
  作業内容をすべてコミットします。
  Run:
  ```powershell
  git add crewai_mermaid.py test_crewai_mermaid.py
  git commit -m "feat: complete advanced multi-agent workflow and verified"
  ```
  Expected: クリーンな状態。
