# Antigravity OS ナレッジドキュメント: Git完全ハンドリング（未プッシュ変更の検出とGitHub自動同期）

---

## 📋 1. 前提情報 (選択能力・メタデータ)

| 項目 | 内容 |
| :--- | :--- |
| **領域** | ソフトウェア開発・エンジニアリング領域 |
| **タイトル** | Git完全ハンドリング (未プッシュ変更の検出と自動同期) |
| **できること** | コミット、ブランチ切り替え、競合解消、未プッシュコミット・ローカル専用ブランチの自律検出とGitHub自動同期 |
| **実例** | リモートとローカルの差分（aheadコミット、未トラッキングブランチ）を自動判定し、設定ポリシーに応じて `git push` を実行 |
| **リソース** | Antigravity OS 内部対話ログ & Gitハンドリングモジュール |
| **関連ドキュメント** | [OKF実践活用ガイド](file:///C:/Users/PC_User/OKF/okf_practical_usage.md) \| [OKF仕様・運用ガイド](file:///C:/Users/PC_User/OKF/okf_specification_overview.md) \| [OKF AIブレイン構築ガイド](file:///C:/Users/PC_User/OKF/okf_brain_build_guide.md) \| [多変量解析自動実行](file:///C:/Users/PC_User/OKF/multivariate_analysis.md) |
| **全体目次** | [OKFナレッジインデックス (INDEX.md)](file:///C:/Users/PC_User/OKF/INDEX.md) |

---

## 🔬 2. よっちゃん流ハイブリッド診断 (分析＆未来ベクトル)

### 🧠 Karpathy流「8つの視点」によるシステム評価
1. **Software 1.0 / 2.0 / 3.0 の共存**: 確定的な Git CLI コマンド (1.0) を基盤とし、差分解析スクリプト (2.0) と、ユーザーの意図判定・ポリシー選択を行う LLM エージェント (3.0) を高度に融合。
2. **LLM as an OS**: エージェントがバックグラウンドプロセス（Cronやタイマートリガー）のようにGitの状態を常時監視・同期。
3. **部分的自律性 (スライダー)**: `main` ブランチは完全自動プッシュ、`feature/*` ブランチは確認ダイアログ経由など、信頼度・環境に応じた制御スライダーを搭載。
4. **アイアンマンスーツ (拡張)**: 開発者が手動で `git status` や `git push` を確認・打鍵する手間を排除し、人間の思考を開発そのものに集中させる。
5. **Vibe Coding (意図)**: 「GitHubに上がってないものを見つけてあげて」という人間の直感的な指示を具体的なGit操作手順へコンパイル。
6. **LLM Psychology (心理学)**: 変更がローカルに閉じ閉塞感を与える不安を解消し、常にリモートへ安全にバックアップ・共有されている安心感を提供。
7. **Compilation Analogy (コンパイル)**: 曖昧な同期リクエストを、`git fetch` → `git branch -vv` → `git push -u` の一連の厳密な実行命令へとトランスパイル。
8. **Build for Agents**: スクリプトの標準出力やリターンコードをモジュール化し、エージェントが自律的にエラーハンドリング・次ステップ判定を行える構造に設計。

### 🧩 内部構造の診断 (核・質・特・欠)

- **核 (核心)**:
  - `git fetch origin` で最新状態を取得後、`git branch -vv`（aheadコミットの抽出）および `git rev-parse --abbrev-ref @{upstream}`（未追跡ブランチの抽出）により未同期状態を確実かつ厳密に検知する仕組み。
- **質 (品質)**:
  - リモート追跡ブランチの有無と先行コミット数（Ahead N）を分離して処理するため、誤ったオーバーライトや不要なプッシュを防止する高い安全性。
- **特 (特性)**:
  - Pythonの `subprocess` モジュールを活用した構造化データの抽出と、ブランチ命名規則（`main`, `feature/*`, `temp-*` など）に基づく柔軟な自動化ポリシー設定。
- **欠 (欠損・課題)**:
  - リモート側と競合（Behindも発生している状態）が起きた場合の自動マージ/コンフリクト解消ロジックが単体スクリプト内では完結していない。

### 🚀 未来ベクトル (方・移・拡・新)

- **方 (方向性)**:
  - 複数エージェントや開発者が分散環境で作業する際の、完全自動・透過的なコード同期エンジンの確立。
- **移 (移動性)**:
  - GitHub だけでなく、GitLab、Bitbucket、Azure DevOps、独自ベアリポジトリ等の全 Git ホスティング環境へそのまま移植可能。
- **拡 (拡張性)**:
  - プッシュ完了時に `gh` CLI と連携して Pull Request を自動作成する機能や、CI/CD テスト結果の自動フィードバック機能への拡張。
- **新 (新規性)**:
  - 開発者がコミットやプッシュコマンドの存在すら意識しない、「完全ノンストップ・シームレス開発環境」の実現。

---

## 💬 3. 対話プロンプト & コンテキスト

### 👤 ユーザープロンプト
> GitHubにあがってないものを見つけて、GitHubにあげてほしいと思います。

### 🤖 Antigravity OS 回答要約
ローカルリポジトリで発生した未プッシュコミットや、GitHub上に存在しない新設ブランチを自律的に検出し、ポリシー（自動実行 / 確認プロンプト / 無視）に基づいて GitHub と自動同期するアプローチと判定スクリプトを提供します。

---

## 💻 4. 実装コード (Python / Git CLI)

### 1. 未プッシュコミット判定スクリプト

```python
import subprocess

def get_unpushed_branches():
    """追跡ブランチより先行(ahead)しているローカルブランチを検出"""
    branches_to_push = []
    try:
        git_cmd = ['git', 'branch', '-vv']
        result = subprocess.run(git_cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        for line in lines:
            branch_info = line.strip().lstrip('* ').strip()
            if "[ahead " in branch_info or ("[origin/" in branch_info and "ahead " in branch_info):
                parts = branch_info.split()
                branch_name = parts[0]
                if any("ahead" in p.lower() for p in parts):
                    branches_to_push.append(branch_name)
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return []
    return branches_to_push
```

### 2. ローカル限定ブランチ検出スクリプト

```python
import subprocess

def get_local_only_branches():
    """リモートに同名ブランチが存在せず、Upstream未設定の純粋ローカルブランチを検出"""
    local_branches = set()
    remote_branches = set()
    final_local_only = []

    try:
        # ローカルブランチ一覧
        res_local = subprocess.run(['git', 'branch', '--format=%(refname:short)'], capture_output=True, text=True, check=True)
        local_branches.update(res_local.stdout.strip().split('\n'))

        # リモートブランチ一覧 (origin/ を除外)
        res_remote = subprocess.run(['git', 'branch', '-r', '--format=%(refname:short)'], capture_output=True, text=True, check=True)
        for r_branch in res_remote.stdout.strip().split('\n'):
            if r_branch.startswith('origin/'):
                remote_branches.add(r_branch[len('origin/'):])

        for branch in local_branches:
            if branch and branch not in remote_branches:
                # Upstreamが設定されているか確認
                try:
                    subprocess.run(['git', 'rev-parse', '--abbrev-ref', branch + '@{upstream}'], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    final_local_only.append(branch)

    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return []

    return final_local_only
```

### 3. 統合実行ロジック (ポリシーベース制御)

```python
def sync_unpushed_changes():
    print("1. リモートの最新情報を取得中...")
    subprocess.run(['git', 'fetch', 'origin'], check=True)

    unpushed = get_unpushed_branches()
    local_only = get_local_only_branches()

    print(f"■ 未プッシュコミットがあるブランチ: {unpushed}")
    print(f"■ ローカルにのみ存在するブランチ: {local_only}")

    # 1. 既存ブランチのプッシュ
    for branch in unpushed:
        if branch == 'main' or branch == 'master':
            print(f"--> [自動実行] {branch} をプッシュします...")
            subprocess.run(['git', 'push', 'origin', branch], check=True)
        elif branch.startswith('temp-'):
            print(f"--> [スキップ] 一時ブランチ {branch} を無視します。")
        else:
            print(f"--> [確認要] {branch} のプッシュ指示を待機します。")

    # 2. 新規ブランチのプッシュ (Upstream設定付き)
    for branch in local_only:
        if not branch.startswith('temp-'):
            print(f"--> [新規作成] {branch} を上流設定付き(-u)でプッシュします...")
            subprocess.run(['git', 'push', '-u', 'origin', branch], check=True)

if __name__ == "__main__":
    sync_unpushed_changes()
```

---

## 📊 5. 運用 & 検証ガイドライン

### 🧪 検証（テスト）手順

1. **未プッシュコミット検出テスト**:
   - テスト用ローカルブランチで新規コミットを作成（プッシュ未実施）。
   - `get_unpushed_branches()` を呼び出し、対象ブランチ名が正確にリストアップされるか確認。

2. **新規ローカルブランチ検出テスト**:
   - `git checkout -b test/new-feature` でローカル限定ブランチを作成。
   - `get_local_only_branches()` を呼び出し、`test/new-feature` が抽出されるか確認。

3. **自動プッシュ動作検証**:
   - `sync_unpushed_changes()` を実行し、`git push origin <branch>` および `git push -u origin <branch>` が正しく発行され、GitHub上のリポジトリに反映されたか確認。
