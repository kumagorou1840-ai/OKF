**<font color="#245bdb">/btw</font>**（By The Way）** は、進行中のメインタスクや会話コンテキストを邪魔せずに、AIへ「ちょっとした補足質問や確認」を挟むためのコマンドです。

- **用途:** 現在の作業状態やコンテキストを汚さず、単発の疑問を解消したいときに使用します。
    
- **特徴:** このコマンドで質問した内容は、以降のメインの文脈（履歴）に引き継がれにくく、一時的なやりとりとして処理されます。
    

**使用例:**

Bash

```
/btw この関数の引数で使える型の一覧を教えて
```

<font color="#ff0000">Antigravity CLI の/btwのコマンドについて代表的な実例を5個表示して。</font>

Antigravity CLIの `/btw`（By the way）コマンドは、メインの処理や文脈を破綻させずに**サイドの補足、一時的な制約の追加、あるいは工学的なパラメータの即時確認**を行うための実用的な機能です。

開発スピードを落とさず、経営的なアジリティと工学的な正確性を両立させるための代表的な実例を5つ挙げます。

### 代表的な実例 5選

1. **一時的な出力フォーマット・制約の追加**
    
    - **コマンド例:** `/btw 出力は日本語のみ、Markdownのテーブル形式で統一して。`
        
    - **意図:** メインの処理フローを維持したまま、表現の揺れや不要な冗長さをその場で防ぐ。
        
2. **技術スタックや構文のピンポイント変更**
    
    - **コマンド例:** `/btw さっきのクエリ、PostgreSQLではなくDuckDBの構文（LIMIT/OFFSET等）に書き換えて。`
        
    - **意図:** 全体のコードを書き直すことなく、特定の部分の環境依存性をその場で修正・適応させる。
        
3. **リソース・コストの即時インパクト確認**
    
    - **コマンド例:** `/btw この処理における推定実行コストとメモリ消費量の見積もりは？`
        
    - **意図:** 経営的・インフラ的なボトルネック（ROIやスケーラビリティ）をリアルタイムで把握し、実装方針を即座に判断する。
        
4. **デバッグログ・詳細情報のトレース要求**
    
    - **コマンド例:** `/btw 次の応答では、内部の例外ハンドリングの挙動とスタックトレースも含めて。`
        
    - **意図:** 工学的なトラブルシューティングの際、余計な手順を踏まずに必要な粒度の高い情報を引き出す。
        
5. **別視点（ペルソナ）からのリスク評価**
    
    - **コマンド例:** `/btw 経営者視点で、このアーキテクチャの最大のスケーラビリティ上のリスクは何？`
        
    - **意図:** 単なるコードの正誤を超え、中長期的なビジネス成長やシステム破綻の予兆を多角的に検証する。
        

特定の自動化ワークフローに合わせたカスタムプロンプト設計を行いますか？

#######################################################

<font color="#245bdb">/usage</font>

**`/usage`** は、現在のセッションにおける**トークン消費量**やAPIの利用状況（クォータ・コスト等）を確認するためのコマンドです。

- **用途:** コンテキストウィンドウの残り容量や、セッションごとのトークン使用率を把握したいときに使用します。
    
- **表示内容:**
    
    - 入力・出力トークン数
        
    - キャッシュされたトークン数
        
    - 現在のコンテキスト上限に対する使用率（%）
        

**使用例:**

Bash

```
/usage
```

<font color="#245bdb">/planning</font>

**`/planning`** は、複雑なタスクや複数ステップにわたる開発作業を行う前に、**AIに作業手順・ロードマップ・影響範囲の事前計画を作成させる**ためのコマンドです。

- **用途:** いきなりコード変更やファイル操作を実行させず、タスクの分解や設計方針を事前にレビュー・調整したいときに使用します。
    
- **特徴:** 作成された計画はステップごとにチェックリスト化され、確認後に `/execute` 等で順次実行へ移すことができます。
    

**使用例:**

Bash

```
/planning DuckDBを使ったデータ集計APIの新規エンドポイント実装
```

<font color="#ff0000">Antigravity CLI の/planningのコマンドについて代表的な実例を5個表示して。</font>

Antigravity CLIの `/planning` コマンドは、実装に入る前に「システムアーキテクチャの整合性」と「ビジネスROI（投資対効果）」を両立させる青写真（ロードマップ）を策定するための強力な指示です。

**現状評価** 多くの開発現場では要件定義や設計をスキップして実装を急ぐあまり、後から技術的負債や仕様変更による手戻りコスト（経営的損失）が発生しがちです。

**不足点** 「作ること」に終始し、例外系の制御、スケーラビリティ、運用コスト、データパイプラインの拡張性が設計段階で抜け落ちています。

**将来性** 事前に工学的制約とビジネス価値を言語化しておくことで、無駄なリファクタリングを防ぎ、機能拡張時の開発速度（Time-to-Market）を最大化できます。

### 代表的な実例 5選

1. **データ分析パイプライン構築の事前設計**
    
    - **コマンド例:** `/planning 大規模な時系列トランザクションデータをDuckDBで集計し、Plotlyで可視化するバッチ処理の全体フローを設計して。`
        
    - **視点:** メモリ効率（工学）とリアルタイムな経営ダッシュボード提供（ビジネス）の最適バランスを定義。
        
2. **堅牢なエラーハンドリングとリトライ戦略の策定**
    
    - **コマンド例:** `/planning 外部API連携時にレート制限やネットワーク切断が発生した際のエクスポネンシャル・バックオフとデッドレターキューの設計案を出して。`
        
    - **視点:** 障害発生時のダウンタイムゼロ化（事業継続性）と通信耐性（耐障害性）を担保。
        
3. **ローカルLLM連携処理のアーキテクチャ設計**
    
    - **コマンド例:** `/planning Ollamaを活用した非同期プロンプト処理基盤のタスクキュー設計と、メモリ使用量の上限管理スキームを策定して。`
        
    - **視点:** インフラコストを抑えつつ、ローカルリソースを枯渇させない安定稼働（ROI最大化）を計画。
        
4. **モジュール分割とクリーンアーキテクチャ化**
    
    - **コマンド例:** `/planning 単一ファイルで肥大化したデータ処理スクリプトを、ドメイン駆動設計（DDD）に基づいてサービス層・リポジトリ層に分離するロードマップを作って。`
        
    - **視点:** 技術的負債を解消し、将来的な複数人開発や機能追加に耐えうる保守性を確保。
        
5. **段階的リリース（フェーズ展開）の計画策定**
    
    - **コマンド例:** `/planning 社内業務自動化ツールのMVP（最小限の機能）から本番運用へ拡張するための3フェーズ開発計画を策定して。`
        
    - **視点:** 早期に初期価値を回収（経営的アジリティ）しながら、段階的に工学的堅牢性を積み上げる。
        

### 改善コード（設計をコードへ落とし込む実装サンプル）

`/planning` で策定された設計（エラー耐性、型安全性、設定分離）を体現したデータ集計タスクの基盤実装です。

Python

```
from dataclasses import dataclass
from typing import Optional
import duckdb
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@dataclass(frozen=True)
class PipelineConfig:
    """経営的視点: リソースと動作パラメータをコードから分離し、運用コストを可視化・制御可能にする"""
    db_path: str = ":memory:"
    memory_limit: str = "2GB"
    threads: int = 4

class ResilientDataPipeline:
    """工学的視点: 型安全・安全なリソース解放・明示的なエラーハンドリングを担保したパイプライン基盤"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self._con: Optional[duckdb.DuckDBPyConnection] = None

    def __enter__(self):
        # 接続の初期化とリソース制限の適用
        self._con = duckdb.connect(self.config.db_path)
        self._con.execute(f"SET memory_limit = '{self.config.memory_limit}'")
        self._con.execute(f"SET threads = {self.config.threads}")
        logging.info("Pipeline connection established with configured resource limits.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # リソースの確実なクリーンアップ
        if self._con:
            self._con.close()
            logging.info("Pipeline connection closed cleanly.")

    def execute_aggregate(self, query: str) -> duckdb.DuckDBPyRelation:
        """安全なクエリ実行と異常系の捕捉"""
        if not self._con:
            raise RuntimeError("Database connection is not open.")
        try:
            logging.info("Executing aggregate pipeline step...")
            result = self._con.sql(query)
            return result
        except duckdb.Error as e:
            logging.error("Database operation failed: %s", e)
            raise

# 実行エントリポイント
if __name__ == "__main__":
    config = PipelineConfig()
    
    # コンテキストマネージャによる確実なライフサイクル管理
    with ResilientDataPipeline(config) as pipeline:
        sample_query = """
            SELECT 
                'Real Estate Asset' AS category, 
                COUNT(*) AS total_records,
                CURRENT_TIMESTAMP AS processed_at
        """
        output = pipeline.execute_aggregate(sample_query)
        output.show()
```

この設計をベースに、具体的なビジネス課題の自動化パイプラインを組み立てますか？

##############################################################
<font color="#245bdb">/exit</font>

**`/exit`** は、現在実行中の対話（Chat）セッションを**安全に終了して元のターミナル／シェルに戻る**ためのコマンドです。

- **用途:** CLIでの作業を終えるときや、シェル環境での通常操作に戻りたいときに使用します。
    
- **エイリアス（同等コマンド）:** `/quit`、または `Ctrl + C` / `Ctrl + D`
    

**使用例:**

Bash

```
/exit
```

<font color="#245bdb">/quit</font>

**`/quit`** は、`/exit` と同様に対話セッションを終了して**シェルに戻るための終了コマンド**です。

- **用途:** 作業の終了、または別のCLIタスクへ移行したいときに使用します。
    
- **エイリアス:** `/exit`（動作は同一です）
    

**使用例:**

Bash

```
/quit
```