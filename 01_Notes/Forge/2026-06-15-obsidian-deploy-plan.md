# 📋 Obsidian to Cloud Spark Deployer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a script that reads a mathematical LaTeX-containing Markdown file from a simulated Obsidian Vault, extracts PySpark code using Antigravity, compiles it, and deploys it to GCP Dataproc Serverless.

**Architecture:** A control script `obsidian_deploy.py` will handle reading the spec file, querying `agy` with the mathematical description and code generation prompt, writing the result to `generated_spark_job.py`, compiling it, and generating/executing the `gcloud` deployment command.

**Tech Stack:** Python (pyspark, subprocess)

---

### Task 1: Create Simulated Obsidian Note

**Files:**
- Create: `scratch/obsidian_vault/saporo_rent_spec.md`

- [ ] **Step 1: Write the simulated Obsidian technical memo**

Create the directories and save the file `scratch/obsidian_vault/saporo_rent_spec.md` with formulaic LaTeX requirements.

Code content for the file:
```markdown
# 札幌市マンション家賃の距離加重平均集計

駅からの距離 $d$ (分) が近い物件ほど家賃 $r$ (万円) の重要度を高く評価するため、以下の数式に基づく加重平均家賃 $W$ を算出する。

加重平均家賃 $W$ の定義：
$$W = \frac{\sum_{i=1}^{n} (r_i \times w_i)}{\sum_{i=1}^{n} w_i}$$
ただし、重み $w_i$ は以下のように定義する：
$$w_i = \frac{1}{d_i + 1}$$

## 要件
1. 札幌のマンションデータ（`data.csv`）を読み込む。
2. 上記の数式に基づいて加重平均家賃を算出し、コンソールに表示する。
3. 結果を CSV 形式で `scratch/weighted_rent_output` に出力する。
```

- [ ] **Step 2: Commit note**

Run:
```bash
git add scratch/obsidian_vault/saporo_rent_spec.md
git commit -m "test: add mock obsidian note for spark deployer"
```

---

### Task 2: Create Deployer Script

**Files:**
- Create: `scratch/obsidian_deploy.py`

- [ ] **Step 1: Implement scratch/obsidian_deploy.py**

Create the deployer script that reads the note, invokes `agy` with a precise parser prompt, saves the output, compiles the generated script, and executes a dry-run / real deploy of the Dataproc batch job.

Code content for `scratch/obsidian_deploy.py`:
```python
# scratch/obsidian_deploy.py
import os
import re
import sys
import subprocess

# Configure stdout to use UTF-8 to prevent cp932 EncodingErrors on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    note_path = "scratch/obsidian_vault/saporo_rent_spec.md"
    generated_path = "scratch/generated_spark_job.py"
    
    print("📖 1. Obsidian技術メモを読み込んでいます...")
    if not os.path.exists(note_path):
        print(f"❌ エラー: 技術メモが見つかりません: {note_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(note_path, "r", encoding="utf-8") as f:
        spec_content = f.read()

    print("🧠 2. Antigravity を呼び出して PySpark コードを抽出中...")
    prompt = (
        "あなたはシニアデータエンジニアです。以下のMarkdownに記述された集計ロジックと数式を完全に理解し、"
        "同一の処理を行う PySpark (Spark 3.5) のコードのみを出力してください。\n\n"
        "【ルール】\n"
        "- 余計な解説やマークダウン以外のテキストは一切出力せず、```python と ``` のブロックのみを出力してください。\n"
        "- 入力ファイル名は 'data.csv'、出力は 'scratch/weighted_rent_output' に保存するようにしてください。\n"
        "- 重み w_i = 1 / (distance + 1) や加重平均の数式を正しく Spark SQL または DataFrame API で実装してください。\n\n"
        f"【技術メモ】\n{spec_content}"
    )

    # agy CLIを実行してコードを生成させる
    try:
        process = subprocess.run(
            ["agy", "--print", prompt, "--dangerously-skip-permissions"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            check=True
        )
        ai_output = process.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Antigravity CLI でエラーが発生しました:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

    # Markdownブロックからコードを抽出
    code_match = re.search(r'```python\s*(.*?)\s*```', ai_output, re.DOTALL)
    if code_match:
        spark_code = code_match.group(1)
    else:
        spark_code = ai_output.strip()

    print(f"💾 3. 生成された PySpark コードを '{generated_path}' に保存しています...")
    os.makedirs(os.path.dirname(generated_path), exist_ok=True)
    with open(generated_path, "w", encoding="utf-8") as f:
        f.write(spark_code)

    print("⚙️ 4. 生成コードの構文検証（コンパイルチェック）を行っています...")
    try:
        import py_compile
        py_compile.compile(generated_path, doraise=True)
        print("✅ 構文チェック成功！エラーはありません。")
    except Exception as e:
        print(f"❌ コンパイルエラーを検出しました:\n{e}", file=sys.stderr)
        sys.exit(1)

    print("🚀 5. GCP Dataproc Serverless Spark へデプロイ中...")
    # デプロイコマンドの組み立て (GCPプロジェクトやバケットは環境変数またはプレースホルダーから)
    project_id = os.environ.get("GCP_PROJECT", "sample-gcp-project")
    region = os.environ.get("GCP_REGION", "asia-northeast1")
    gcs_bucket = os.environ.get("GCS_BUCKET", "saporo-rent-pipeline-bucket")
    
    # 実際のデプロイでは、コードをGCSにアップロードし、Dataproc Batchesを実行します
    deploy_cmd = [
        "gcloud", "dataproc", "batches", "submit", "pyspark",
        f"gs://{gcs_bucket}/jobs/generated_spark_job.py",
        f"--project={project_id}",
        f"--region={region}",
        f"--deps-bucket=gs://{gcs_bucket}"
    ]
    
    print("\n📦 [デプロイコマンド]")
    print(" ".join(deploy_cmd))
    
    # テスト環境（本番GCP未設定時）は、dry-run としてコマンドの組み立て検証で正常終了します
    if "GCS_BUCKET" not in os.environ:
        print("\n⚠️ 環境変数 GCS_BUCKET が設定されていないため、デプロイコマンドの組み立て確認（Dry-run）のみで終了します。")
        print("🎉 自動デプロイパイプラインの準備が完了しました！")
    else:
        # GCSへのアップロードとジョブ投入の実行
        print("📤 スクリプトを GCS にアップロード中...")
        upload_cmd = ["gcloud", "storage", "cp", generated_path, f"gs://{gcs_bucket}/jobs/generated_spark_job.py"]
        subprocess.run(upload_cmd, check=True)
        print("⏳ Dataproc Batch ジョブを投入中...")
        subprocess.run(deploy_cmd, check=True)
        print("🎯 GCP へのデプロイが成功しました！")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit script**

Run:
```bash
git add scratch/obsidian_deploy.py
git commit -m "feat: add obsidian deployer script"
```

---

### Task 3: Verify and Test Execution

**Files:**
- Test: `scratch/obsidian_deploy.py`

- [ ] **Step 1: Execute deployer script**

Run:
```pwsh
python scratch/obsidian_deploy.py
```
Expected: The script executes step-by-step, retrieves Spark code from `agy` successfully, compiles without syntax error, and prints the simulated `gcloud` deploy command, finishing with "Dry-run" completion message.

- [ ] **Step 2: Verify generated PySpark code**

Read the output code in `scratch/generated_spark_job.py` to ensure it implements weight distance-based calculation logic as described.
