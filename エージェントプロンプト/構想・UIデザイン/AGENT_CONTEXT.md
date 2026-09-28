# AGENT_CONTEXT

## 📌 プロジェクト概要
* **プロジェクト名**: Anthropic `knowledge-work-plugins` 調査
* **背景**: Claude Cowork / Code 向けに公開されている18種類の専門分野（分類）のプラグインの調査および詳細把握。
* **ユーザー (Owner)**: よっちゃん

---

## ⚙️ ユーザー設定 & ルール (重要)
次回以降のセッションでも、以下のパーソナル設定および職人厳守ルールを必ず適用すること。
* **言語設定**: すべて日本語で対応する。
* **呼称**: ユーザーを「よっちゃん」と呼ぶ。
* **パーソナル設定**: 設定（Settings）情報やヘルプ内容は、常に日本語で分かりやすく翻訳・解説して提供する。
* **思考プロセス**: 抽象と具体の往復を行う。
* **ハイブリッド診断フレームワーク**: 
  1. Karpathy流「8つの視点」（Software 1.0/2.0/3.0共存、LLM as an OS、部分的自律性、アイアンマンスーツ、Vibe Coding、LLM Psychology、Compilation Analogy、Build for Agents）
  2. 分析視点「核・質・特・欠」（現状診断）
  3. 未来ベクトル「方・移・拡・新」（進化方向性）
  これらを組み合わせた多角的なシステム評価を標準適用する。
* **職人としての厳守ルール**:
  1. **Surgical Changes（外科的修正）**: 指示された箇所以外（スペース、クォート、無関係な行）は1文字も変えない。
  2. **Simplicity First**: 複雑な抽象化を避け、最もシンプルに実装する。
  3. **Think Before Coding**: 実装前に必ず「前提条件の確認」をよっちゃんに1つ以上行う。
  4. **Goal-Driven**: 実装後は必ず「検証（テスト）方法」を提示し、よっちゃんの確認を得る。

---

## 📈 現在のステータス & 成果物
* **ステータス**: 18種類すべてのプラグイン詳細調査、格納ファイル調査、および各種ユースケース抽出を完了。
* **よっちゃんからの追加リクエスト**:
  - 18分野のそれぞれの内容と、その中に含まれているファイルを表示してほしいです。
  - それぞれの分野の代表的なものを30個、表示してほしいです。
* **成果物一覧（Antigravity CLIでそのまま活用可能）**:
  * **初期レポート (18分野の役割・コネクター要約)**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/knowledge_work_plugins_details.md`
  * **Bio-Research（バイオ研究）における現実の代表的な研究アプローチ 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_bio_research_30_methods.md`
  * **Cowork Plugin Management（プラグイン管理）における現実の代表的な管理アプローチ 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_plugin_management_30_methods.md`
  * **Customer Support（カスタマーサポート）における現実の代表的な対応アプローチ 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_customer_support_30_methods.md`
  * **Data Analyst（データアナリスト）における現実の代表的なデータ分析アプローチ 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_data_analyst_30_methods.md`
  * **B: 各分野ごとの全格納ファイル ＆ 分野内組み合わせ30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_combinations_B.md`
  * **C: 現実世界で代表的な・重要な機能ファイル（スキル）30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_C_top_30_skills.md`
  * **A: 18分野を横断した代表的な組み合わせ30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_A_cross_domain_30_scenarios.md`
  * **account-research（顧客企業調査）における現実の代表的な調査観点 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_account_research_30_methods.md`
  * **call-prep（商談の事前準備）における現実の代表的な準備事項 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_call_prep_30_methods.md`
  * **call-summary（商談要約・議事録作成）における現実の代表的な要約項目 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_call_summary_30_methods.md`
  * **competitive-intelligence（競合分析）における現実の代表的な比較分析観点 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_competitive_intelligence_30_methods.md`
  * **create-an-asset（営業資料・アセット作成）における現実の代表的な営業アセット 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_create_an_asset_30_methods.md`
  * **daily-briefing（営業日報・活動要約）における現実の代表的な構成項目 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_daily_briefing_30_methods.md`
  * **draft-outreach（アプローチメールの下書き）における現実の代表的なメールアプローチ 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_draft_outreach_30_methods.md`
  * **forecast（売上予測・フォーキャスト）における現実の代表的な予測モデル 30選**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/28a320ba-842f-4643-9798-1fb6481f609c/plugins_forecast_30_methods.md`
  * **科学的仮説選択エージェントシステム プロンプト設計仕様書**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/6b8eb6bd-d514-47d9-8bf6-b1f3e23c1164/2026-07-12-scientific-hypothesis-selection-design.md`
  * **科学的仮説選択エージェントシステム 実装計画書**:
    * パス: `C:/Users/PC_User/.gemini/antigravity-cli/brain/6b8eb6bd-d514-47d9-8bf6-b1f3e23c1164/2026-07-12-scientific-hypothesis-selection-plan.md`
  * **科学的仮説選択エージェントシステム 実装コード**:
    * パス: `C:/Users/PC_User/Forge/run_scientific_hypothesis.py`
  * **科学的仮説選択エージェントシステム テストコード**:
    * パス: `C:/Users/PC_User/Forge/test_scientific_hypothesis.py`

---

## ⏭️ 次のアクション
1. よっちゃんによる詳細レポートの確認と検証。
2. 業務・自社組織に合わせたプラグインのカスタマイズ（`.mcp.json` やスキルファイルの調整）の方針決定。
