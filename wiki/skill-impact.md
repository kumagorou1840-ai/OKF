# Skill Impact Log

| Iteration | Skill Target | Action | Baseline Acc | Candidate Acc | Result | Diff Link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| iter-01 | `data-extraction` | Add fallback retry | 48.7% | 53.2% | **ACCEPTED** | [[diff-iter-01]] |
| iter-02 | `data-extraction` | Force JSON schema | 53.2% | 49.0% | **REJECTED** | [[diff-iter-02]] |

## iter-02 Rejection Details
- **Reason**: 厳格すぎるスキーマ検証により、一部のAPI応答でタイムアウトが発生。
- **Wiki Pattern Linked**: [[wiki/patterns/PAT-001_context-overflow]]
- **Lesson**: スキーマ検証は出力パース時のみに限定し、通信プロトコルには適用しないこと。
| iter-03 | `data-extraction` | Strict regex validation | 53.2% | 47.8% | **REJECTED** | [[diff-iter-03]] |

### iter-03 Rejection Details
- **Reason**: regex-backtracking-timeout
- **Wiki Pattern Linked**: [[wiki/patterns/PAT-002_regex-backtracking-timeout]]
- **Lesson**: 正規表現による完全一致検証を廃止し、トークンベースの分割パースを採用すること。

| iter-03 | `data-extraction` | Strict regex validation | 53.2% | 47.8% | **REJECTED** | [[diff-iter-03]] |

### iter-03 Rejection Details
- **Reason**: regex-backtracking-timeout
- **Wiki Pattern Linked**: [[wiki/patterns/PAT-003_regex-backtracking-timeout]]
- **Lesson**: 正規表現による完全一致検証を廃止し、トークンベースの分割パースを採用すること。

| iter-04 | `data-extraction` | Token-based stream parsing | 47.8% | 65.4% | **ACCEPTED** | [[diff-iter-04]] |

### iter-04 Acceptance Details
- **Action**: Token-based stream parsing
- **Accuracy Gain**: 47.8% -> 65.4%
- **Resolved Wiki Pattern**: [[wiki/patterns/PAT-002_regex-backtracking-timeout]]


| iter-04 | `data-extraction` | 正規表現によるJSON要素抽出失敗とタイムアウト | - | - | **REJECTED** | [[diff-iter-04]] |

### iter-04 Rejection Details
- **Reason**: 入力データからの物件名・家賃のJSONフォーマット抽出において、使用されている正規表現が実際の入力データ形式と一致していなかった、または入力テキストが非常に長く、非効率的な正規表現パターンがバックトラックを引き起こし、正規表現エンジンの処理がタイムアウトしたことが根本原因です。JSONのような構造化データを正規表現でパースしようとすること自体が、堅牢性とパフォーマンスの観点から問題となる場合があります。
- **Wiki Pattern Linked**: [[wiki/patterns/PAT-004_regex-json-timeout]]
- **Lesson**: 再発防止のためには以下の点に留意してください。
1.  **JSONパーサーの利用**: JSON形式のデータを扱う場合は、正規表現ではなく、各プログラミング言語に標準で用意されているJSONパーサー（例: Pythonの`json`モジュール）を最優先で利用し、データ抽出の正確性と堅牢性を確保する。
2.  **正規表現の見直しとテスト**: 正規表現を使用せざるを得ない場合は、対象となる入力データの多様なパターン（正常系・異常系、エッジケース）を網羅するテストケースを作成し、正規表現が正確にマッチするか、また長文データでも効率的に動作するかを確認する。特に、過度なバックトラックを避けるために非貪欲マッチ（`*?`, `+?`）やアトミックグループ（`(?>...)`）の利用を検討する。
3.  **入力データの検証と制限**: 入力データの最大長を事前に検証し、想定される範囲を超える場合はエラーとして処理するか、データ分割などの前処理を検討する。また、入力データが常に期待されるフォーマットに従っているか確認し、逸脱する場合は適切なエラーハンドリングを行う。
4.  **ロギングの強化**: エラー発生時には、使用された正規表現、失敗した入力テキストの抜粋（またはハッシュ）、処理時間、およびタイムアウトが発生した場合はその旨を詳細にログに出力し、デバッグと原因特定の効率化を図る。

| iter-05 | `data-extraction` | Native JSON parser with pre-validation | 65.4% | 78.2% | **ACCEPTED** | [[diff-iter-05]] |

### iter-05 Acceptance Details
- **Action**: Native JSON parser with pre-validation
- **Accuracy Gain**: 65.4% -> 78.2%
- **Resolved Wiki Pattern**: [[wiki/patterns/PAT-004_regex-json-timeout]]
