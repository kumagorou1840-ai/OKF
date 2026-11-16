#!/usr/bin/env python3
"""
design_action_engine.py
index-13（複素数平面・固有値・非対角成分モデル）と
index-15（49の技術：Right Is Right / What to Do / Do It Again）を統合した実務アクション診断エンジン。

要件:
1. Pydantic v2 による厳格バリデーション（Right Is Right）
2. 複素数平面 z = x + iy・固有値 λ・非対角成分率によるフェーズ＆推奨アクション判定（index-13由来）
3. 入居者案内文・AI指示文の否定形・曖昧表現検知と What to Do 変換提案（index-15由来）
4. Obsidian `06_Reports/YYYY-MM-DD_実務アクション診断レポート.md` への自動出力
"""

from __future__ import annotations

import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


# ============================================================================
# 1. Pydantic v2 スキーマ定義（Right Is Right：曖昧さ・欠落を許さない100%基準）
# ============================================================================

class ComplexMetricsInput(BaseModel):
    """index-13: 複素数平面・固有値モデルの入力データスキーマ"""

    project_name: str = Field(..., min_length=2, description="診断対象のプロジェクト名・案件名")
    domain: Literal["info_output", "real_estate", "ai_dev"] = Field(
        ..., description="実務ドメイン（info_output / real_estate / ai_dev）"
    )
    real_x: float = Field(
        ..., description="実軸 x（実績・ストック資産の現在スコア: -10.0 〜 +10.0）", ge=-10.0, le=10.0
    )
    imag_y: float = Field(
        ..., description="虚軸 y（期待感・初動微分の傾きスコア: -10.0 〜 +10.0）", ge=-10.0, le=10.0
    )
    eigenvalue_lambda: float = Field(
        ..., description="時代の波・顧客ニーズとの同期率（固有値 λ: 0.1 〜 3.0）", ge=0.1, le=3.0
    )
    off_diagonal_ratio: float = Field(
        ..., description="非対角成分（他者との相互作用＝愛）の配分比率（0.0 〜 1.0）", ge=0.0, le=1.0
    )
    instruction_text: str = Field(
        ..., min_length=10, description="検証対象の案内文（入居者向け）またはAI指示プロンプト"
    )

    @field_validator("project_name", "instruction_text")
    @classmethod
    def check_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("【Right Is Right 違反】空白のみの文字列は許可されません。")
        return cleaned

    @model_validator(mode="after")
    def check_zero_origin(self) -> "ComplexMetricsInput":
        if self.real_x == 0.0 and self.imag_y == 0.0:
            raise ValueError(
                "【Right Is Right 違反】実軸(x)と虚軸(y)がともに0.0です。現状の実績または初動の傾きを測定して入力してください。"
            )
        return self


# ============================================================================
# 2. 数理診断エンジン（index-13: 複素数 z = x + iy × 固有値 λ × 非対角成分）
# ============================================================================

class MathDiagnosisResult(BaseModel):
    """数理診断の出力モデル"""

    z_str: str
    magnitude_r: float
    angle_deg: float
    effective_growth_score: float
    phase: Literal["🌅 停滞期（夜明け前）", "🚀 成長期", "👑 成熟期", "🌇 後退期（終わりの始まり）"]
    balance_assessment: str
    recommended_action: str


def evaluate_math_model(data: ComplexMetricsInput) -> MathDiagnosisResult:
    """複素数 z = x + iy の回転角・絶対値・固有値・非対角成分からフェーズと行動を導出"""
    x = data.real_x
    y = data.imag_y
    lam = data.eigenvalue_lambda
    off_diag = data.off_diagonal_ratio

    # 複素数の絶対値 r と偏角 θ (度)
    r = math.hypot(x, y)
    angle_rad = math.atan2(y, x)
    angle_deg = math.degrees(angle_rad)

    # 非対角成分の黄金比（対角70% : 非対角30%）からのボーナス係数
    harmony_factor = 1.15 - abs(off_diag - 0.30) * 0.8
    harmony_factor = max(0.75, min(1.15, harmony_factor))

    # 実効成長モメンタムスコア
    effective_growth = round(r * lam * harmony_factor, 2)

    # 4象限による「仏の目」フェーズ判定
    if x < 2.0 and y >= 0.0:
        phase: Literal["🌅 停滞期（夜明け前）", "🚀 成長期", "👑 成熟期", "🌇 後退期（終わりの始まり）"] = (
            "🌅 停滞期（夜明け前）"
        )
        action = (
            "【攻めの投資】実数(x)はまだ小さいですが、虚数(y:初動傾き)がプラスで左上へ回転中です。"
            "早すぎる撤退を避け、現在の専門性（固有ベクトル）への集中投資を継続してください。"
        )
    elif x >= 2.0 and y >= 2.5:
        phase = "🚀 成長期"
        action = (
            "【非対角成分の拡大と加速】実数(x)と虚数(y)がともに高く、固有値による指数関数的成長フェーズです。"
            "他者との共創・丁寧なサポート（非対角成分）を30%枠で回し、系全体の固有値をさらに引き上げてください。"
        )
    elif x >= 2.0 and 0.0 <= y < 2.5:
        phase = "👑 成熟期"
        action = (
            "【次なる虚数（新テーマ）の種まき】実績(x)は盤石ですが、初動の傾き(y)が巡航速度に落ち着いています。"
            "後退期へ入る前に、新しい時代の波（高固有値テーマ）との掛け合わせ実験を1割〜2割で開始してください。"
        )
    else:
        phase = "🌇 後退期（終わりの始まり）"
        action = (
            "【撤退・モデル修正（Fast-Fail）】虚数(y:期待感・初動傾き)がマイナスへ転じ、右下へ回転しています。"
            "過去の実績(x)に慢心・固執せず、速やかにピボット（構造改革・新モデル移行）を断行してください。"
        )

    # 非対角成分（相互作用＝愛）のバランス診断
    if off_diag < 0.15:
        balance_msg = (
            f"⚠️ 孤立傾向（非対角比率 {off_diag:.0%}）：対角成分（自力作業）に偏りすぎています。"
            "返信・配慮・異分野連携（愛）を30%まで増やして固有値を増幅させましょう。"
        )
    elif off_diag > 0.45:
        balance_msg = (
            f"⚠️ 過剰分散リスク（非対角比率 {off_diag:.0%}）：他者対応や枝葉の活動に時間を奪われ、"
            "コア業務（対角成分）が希薄化しています。『対角70%：非対角30%』の黄金比へ戻しましょう。"
        )
    else:
        balance_msg = (
            f"✅ 黄金比達成（非対角比率 {off_diag:.0%}）：コア専門性（対角）と他者への貢献（非対角＝愛）が"
            "理想的なバランスで共鳴しています。"
        )

    sign_str = "+" if y >= 0 else "-"
    z_str = f"{x:.1f} {sign_str} {abs(y):.1f}i"

    return MathDiagnosisResult(
        z_str=z_str,
        magnitude_r=round(r, 2),
        angle_deg=round(angle_deg, 1),
        effective_growth_score=effective_growth,
        phase=phase,
        balance_assessment=balance_msg,
        recommended_action=action,
    )


# ============================================================================
# 3. 指導・案内文チェッカー（index-15: What to Do / Right Is Right / Warm-Strict）
# ============================================================================

FORBIDDEN_PATTERNS: List[Tuple[str, str, str, str]] = [
    (
        r"しないでください|しないで下さい|やめてください|禁止です",
        "否定形指示（What NOT to Do）",
        "「〜するな」という否定形は、相手が「代わりに具体的に何をすべきか」を瞬時にイメージできず遵守率が下がります。",
        "【What to Do 変換】「〇〇の代わりに、［具体的な時刻/場所］に［観察可能な肯定行動］を行ってください」へ書き換える。",
    ),
    (
        r"なるべく|できるだけ|可能な限り",
        "曖昧な努力目標（Right Is Right 違反）",
        "基準が受け手の主観に委ねられるため、70点の妥協や未達を生みます。",
        "【Right Is Right 変換】「〇〇時までに」「〇〇分以内に」「100%」など測定可能な数値基準（4Ms）へ置き換える。",
    ),
    (
        r"適切に|適宜|ちゃんと|しっかり|うまく",
        "抽象的・非観察可能表現（What to Do 違反）",
        "「適切に」の中身が指導者と受け手でズレるため、実行エラーの原因になります。",
        "【Name the Steps 変換】「①〇〇を開く → ②〇〇を入力する → ③〇〇を確認する」の具体的な手順に分解する。",
    ),
    (
        r"気をつけて|注意してください|心がけて",
        "内面・精神論への依存",
        "「気をつける」は外から観察・検証（Check for Understanding）できない指示です。",
        "【観察可能行動への変換】「作業完了後にチェックリストの3項目にレ点を入れて提出してください」など行動で指定する。",
    ),
]


class PhraseIssue(BaseModel):
    matched_text: str
    category: str
    reason: str
    what_to_do_suggestion: str


class InstructionCheckResult(BaseModel):
    is_100_percent_clear: bool
    score: int
    detected_issues: List[PhraseIssue]
    rewritten_example: str


def check_instruction_text(text: str) -> InstructionCheckResult:
    """案内文・プロンプトから否定形・曖昧表現を検知し、What to Do 形式の修正案を生成する"""
    issues: List[PhraseIssue] = []
    rewritten = text

    specific_replacements: Dict[str, str] = {
        "熱湯をかけないでください": "水道管の破損を防ぐため、30〜40℃のぬるま湯をタオルの上からゆっくりかけてください",
        "ゴミを放置しないでください": "収集日当日の朝8時までに、指定の黄色いゴミ袋に入れてゴミステーション内の青いネットの下へ配置してください",
        "夜間に騒がないでください": "22時以降はテレビ・音楽の音量をメモリ2以下に下げ、足音が響かないようスリッパをご着用ください",
        "ミスをしないでください": "提出前に自動検証スクリプト（pytest）を1回実行し、エラー0件を確認してください",
        "なるべく早く": "本日17時までに",
        "なるべく残業を減らし": "18時00分にPCをシャットダウンし",
        "できるだけ早く": "24時間以内に",
        "適切に処理": "Pydanticスキーマで型検証を行い、エラー時はログに出力して再試行",
        "適切に対応": "標準手順書のステップ1〜3に従って対応",
        "ちゃんと確認して": "チェックリストの全3項目を指差し確認して",
        "気をつけてください": "作業前後に3項目の指差し確認を実施してください",
        "注意してください": "室温計が5℃以下になった際は水抜き栓を右へ止まるまで回してください",
    }

    for pattern, category, reason, suggestion in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, text):
            issues.append(
                PhraseIssue(
                    matched_text=match.group(0),
                    category=category,
                    reason=reason,
                    what_to_do_suggestion=suggestion,
                )
            )

    for bad, good in specific_replacements.items():
        if bad in rewritten:
            rewritten = rewritten.replace(bad, f"【What to Do修正: {good}】")

    rewritten = re.sub(r"なるべく|できるだけ", "【4Ms数値基準: 〇時までに/〇件以上】", rewritten)
    rewritten = re.sub(r"適切に|適宜", "【Name the Steps: 手順①〜③に従って】", rewritten)

    score = max(0, 100 - len(issues) * 25)
    return InstructionCheckResult(
        is_100_percent_clear=(len(issues) == 0),
        score=score,
        detected_issues=issues,
        rewritten_example=rewritten,
    )


# ============================================================================
# 4. Markdownレポート生成（Obsidian `06_Reports/` 出力）
# ============================================================================

def generate_markdown_report(
    evaluations: List[Tuple[ComplexMetricsInput, MathDiagnosisResult, InstructionCheckResult]],
    validation_errors: List[Tuple[str, str]],
    output_path: Path,
) -> Path:
    """診断結果を @obsidian-hub 準拠の Markdown レポートとして保存する"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines: List[str] = [
        "---",
        "tags:",
        "  - category/action_diagnosis_report",
        "  - math_science/complex_analysis",
        "  - general_reading/education",
        f"created: {date_str}",
        "status: completed",
        "engine: design_action_engine.py",
        "---",
        "",
        f"# 🎯 実務アクション統合診断レポート ({date_str})",
        "",
        "> [!info] 統合診断エンジンの設計根拠",
        f"> - **実行日時**: `{now_str}`",
        "> - **親ダッシュボード**: [[Cockpit_MOC]] ([Cockpit_MOC.md](../00_Dashboard/Cockpit_MOC.md))",
        "> - **数理モデル基盤 (`index-13`)**: [2026-11-16_数理の目と愛_ビジネスと人生の最適化設計図_要約.md](../03_Resources/2026-11-16_数理の目と愛_ビジネスと人生の最適化設計図_要約.md)",
        "> - **指導・行動設計基盤 (`index-15`)**: [2026-11-16_最高の教師をつくる49の技術_設計書.md](../03_Resources/2026-11-16_最高の教師をつくる49の技術_設計書.md)",
        "",
        "---",
        "",
        "## 📊 1. 全体サマリー（複素平面フェーズ × What to Do 明瞭度）",
        "",
        "| # | プロジェクト・案件名 | ドメイン | 複素数 $z = x + iy$ | 偏角 $\\theta$ | 固有値 $\\lambda$ | 非対角率 | 仏の目フェーズ判定 | 指示文スコア (`Right Is Right`) |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |",
    ]

    for idx, (inp, math_res, inst_res) in enumerate(evaluations, start=1):
        badge = "✅ 100点 (合格)" if inst_res.is_100_percent_clear else f"⚠️ {inst_res.score}点 (要Do It Again)"
        lines.append(
            f"| {idx} | **{inp.project_name}** | `{inp.domain}` | `{math_res.z_str}` | `{math_res.angle_deg}°` | "
            f"`{inp.eigenvalue_lambda:.2f}` | `{inp.off_diagonal_ratio:.0%}` | **{math_res.phase}** | {badge} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 🧭 2. 案件別・詳細診断＆『What to Do』改善提案",
        "",
    ])

    for idx, (inp, math_res, inst_res) in enumerate(evaluations, start=1):
        lines.extend([
            f"### 📌 案件 {idx}: {inp.project_name} (`{inp.domain}`)",
            "",
            "#### (A) 【数理の目と愛 (`index-13`)】複素平面・固有値・非対角診断",
            f"- **状態ベクトル**: $z = {math_res.z_str}$ （絶対値 $r = {math_res.magnitude_r}$, 回転角 $\\theta = {math_res.angle_deg}°$）",
            f"- **時代・顧客同期率（固有値 $\\lambda$）**: `{inp.eigenvalue_lambda:.2f}` ／ **実効成長スコア**: `{math_res.effective_growth_score}`",
            f"- **フェーズ判定**: **{math_res.phase}**",
            f"- **非対角成分（相互作用＝愛）評価**: {math_res.balance_assessment}",
            "",
            "> [!tip] 推奨アクション（数理モデルからの導出）",
            f"> {math_res.recommended_action}",
            "",
            "#### (B) 【49の技術 (`index-15`)】案内文・指示文『What to Do / Right Is Right』監査",
            f"- **元の指示・案内文**:",
            f"  > 「{inp.instruction_text}」",
        ])

        if inst_res.is_100_percent_clear:
            lines.extend([
                "- **監査判定**: ✅ **`Right Is Right` 合格（100点）** — 否定形や曖昧表現を含まず、観察可能な具体行動で記述されています。",
                "",
            ])
        else:
            lines.append(f"- **監査判定**: ⚠️ **`Do It Again`（やり直し推奨：{inst_res.score}点 / {len(inst_res.detected_issues)}件の曖昧・否定表現を検知）**")
            lines.append("")
            for issue in inst_res.detected_issues:
                lines.append(f"  - ❌ **検知語句**: `「{issue.matched_text}」` （分類: *{issue.category}*）")
                lines.append(f"    - **理由**: {issue.reason}")
                lines.append(f"    - **改善指針**: {issue.what_to_do_suggestion}")
            lines.extend([
                "",
                "> [!important] 『Warm/Strict × What to Do』自動書き換え提案",
                f"> 「{inst_res.rewritten_example}」",
                "",
            ])

        lines.append("---")
        lines.append("")

    # 3. Pydantic Right Is Right バリデーション差し戻しログ
    lines.extend([
        "## 🛡️ 3. 『Right Is Right』Pydantic 厳格ゲート検証ログ（曖昧・欠落データの即時差し戻し）",
        "",
        "> [!warning] 第1層ガードレール（No Opt Out / Right Is Right）",
        "> 曖昧な数値や空白テキスト、原点 `(0, 0)` の未計測データは、下流へ流さず Pydantic v2 バリデータで100%即時差し戻します。",
        "",
    ])

    for case_title, err_msg in validation_errors:
        lines.append(f"- **テストケース `{case_title}`**: 🛑 **即時差し戻し成功**")
        lines.append(f"  - 検出エラー: `{err_msg}`")

    lines.extend([
        "",
        "---",
        "",
        "## ✅ 4. 次の実務アクション（Exit Ticket）",
        "- [ ] 案件1（冬期水道凍結案内）の『What to Do 書き換え案』を `mail_triage_bot.py` の返信テンプレートへ反映する",
        "- [ ] 案件2（NotebookLM Architect 発信）の非対角成分（28%）を維持し、30日後の実数化（反響増）を計測する",
        "- [ ] 案件3（レガシー手動集計フロー）の後退期ピボットとして、Python自動集計スクリプトへの完全移行を完了させる",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ============================================================================
# 5. メイン実行・自己検証テストスイート
# ============================================================================

def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    print("=" * 72)
    print("🚀 Design Action Engine (index-13 数理モデル × index-15 49の技術) 起動")
    print("=" * 72)

    raw_test_cases = [
        {
            "project_name": "北海道・冬期水道凍結予防＆入居者トリアージ体制",
            "domain": "real_estate",
            "real_x": 1.2,               # 導入初期で実績はまだこれから
            "imag_y": 4.8,               # 初動の反応・自動化精度の傾きが急上昇中
            "eigenvalue_lambda": 1.45,   # 冬期需要（季節の波）と完全同期
            "off_diagonal_ratio": 0.30,  # 入居者への温かい配慮30% : 厳格な契約管理70%
            "instruction_text": (
                "冬場は水道管が凍結しやすいため注意してください。"
                "万が一凍った場合でも、絶対に熱湯をかけないでください。なるべく早く管理会社へ連絡し、適切に対応してください。"
            ),
        },
        {
            "project_name": "NotebookLM × Obsidian 実践設計書（@notebooklm-architect）発信",
            "domain": "info_output",
            "real_x": 5.5,               # すでに複数の高品質ノートが蓄積
            "imag_y": 6.2,               # 初動の熱量・応用展開の勢いが非常に高い
            "eigenvalue_lambda": 1.60,   # AIエージェント時代の波と強く共鳴
            "off_diagonal_ratio": 0.28,  # 黄金比（対角72% : 非対角28%）
            "instruction_text": (
                "毎朝8時までにNotebookLMの対象IDを1つ指定し、3大要点・外部比較表・実務トラッカーを含む"
                "Markdown設計書を03_Resourcesフォルダへ保存してCockpit_MOCのリンクを100%更新してください。"
            ),
        },
        {
            "project_name": "旧来の手動コピペによる月次データ集計作業",
            "domain": "ai_dev",
            "real_x": 6.0,               # 過去の蓄積実績はある
            "imag_y": -3.5,              # 期待感・効率の傾きはマイナス（右下へ回転）
            "eigenvalue_lambda": 0.55,   # AI自動化時代の波から逆行
            "off_diagonal_ratio": 0.05,  # 孤立した単純作業
            "instruction_text": "ミスをしないでください。月末はなるべく残業を減らし、データをちゃんと確認して適切に処理してください。",
        },
    ]

    evaluations: List[Tuple[ComplexMetricsInput, MathDiagnosisResult, InstructionCheckResult]] = []

    for raw in raw_test_cases:
        validated = ComplexMetricsInput.model_validate(raw)
        math_res = evaluate_math_model(validated)
        inst_res = check_instruction_text(validated.instruction_text)
        evaluations.append((validated, math_res, inst_res))
        print(f"\n✅ 診断完了: 【{validated.project_name}】")
        print(f"   ├─ 複素数 z = {math_res.z_str} (r={math_res.magnitude_r}, θ={math_res.angle_deg}°) -> {math_res.phase}")
        print(f"   ├─ 実効成長スコア: {math_res.effective_growth_score} | {math_res.balance_assessment[:32]}...")
        print(f"   └─ 指示文監査スコア: {inst_res.score}点 (禁止表現検知: {len(inst_res.detected_issues)}件)")

    # Right Is Right (Pydantic v2 厳格差し戻し) のテスト
    invalid_cases = [
        (
            "原点(0,0)未計測データの投入テスト",
            {
                "project_name": "未計測プロジェクト",
                "domain": "info_output",
                "real_x": 0.0,
                "imag_y": 0.0,
                "eigenvalue_lambda": 1.0,
                "off_diagonal_ratio": 0.3,
                "instruction_text": "十分な長さのあるテスト指示文です。",
            },
        ),
        (
            "空白指示文・固有値レンジ外の投入テスト",
            {
                "project_name": "異常値テスト",
                "domain": "real_estate",
                "real_x": 2.0,
                "imag_y": 1.0,
                "eigenvalue_lambda": 9.9,  # 上限3.0超過
                "off_diagonal_ratio": 0.3,
                "instruction_text": "   ",
            },
        ),
    ]

    validation_errors: List[Tuple[str, str]] = []
    print("\n🛡️ Right Is Right (Pydantic v2 バリデーション差し戻しテスト):")
    for title, bad_payload in invalid_cases:
        try:
            ComplexMetricsInput.model_validate(bad_payload)
        except ValidationError as exc:
            first_msg = exc.errors()[0]["msg"]
            validation_errors.append((title, first_msg))
            print(f"   ├─ 🛑 差し戻し成功 [{title}]: {first_msg}")

    # Obsidian 06_Reports へレポート出力
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = Path(r"C:\Users\PC_User\Obsidian_2\06_Reports") / f"{date_str}_実務アクション診断レポート.md"
    saved_path = generate_markdown_report(evaluations, validation_errors, report_path)

    print("\n" + "=" * 72)
    print(f"📄 Obsidian レポート出力完了: {saved_path}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
