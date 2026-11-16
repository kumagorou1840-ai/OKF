# 二値（Bool）、段階（Scale）、確率（Probability）を3段パイプラインで直列実行し、
# 早期打ち切り（Fast-Fail）および 3レーン自動仕分け（AUTO_APPROVE / HUMAN_REVIEW / AUTO_REJECT）を行う
# 「完全版ハイブリッドJev監査器（jev_hybrid_auditor.py）」のコードです。
import sys
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any

# ==============================================================================
# 0. パス設定 (Obsidian_2 ディレクトリ)
# ==============================================================================
BASE_DIR = Path("G:/マイドライブ/Obsidian_2")
REPORTS_DIR = BASE_DIR / "06_Reports"
DASHBOARD_FILE = BASE_DIR / "00_Dashboard" / "Jev_Audit_Dashboard.md"

# ==============================================================================
# 1. 監査データ構造
# ==============================================================================

@dataclass
class BoolAuditResult:
    passed: bool
    has_apology: bool             # 冒頭のお詫び・共感の有無
    has_cause_investigation: bool # 原因確認先行（安易な全額負担確約の禁止）
    has_action_schedule: bool     # 具体的な行動・日程打診の提示
    reason: str

@dataclass
class ScaleAuditResult:
    passed: bool
    skipped: bool              # 第1層Fast-Failによるスキップ有無
    empathy_level: int         # 1〜5
    risk_control_level: int    # 1〜5
    action_clarity_level: int  # 1〜5
    average_score: float
    grade: str                 # S / A / B / C / SKIPPED
    reason: str

@dataclass
class ProbAuditResult:
    passed: bool
    skipped: bool                   # 第1層Fast-Failによるスキップ有無
    trouble_escalation_prob: float  # 炎上・二次クレーム確率 (閾値 <= 0.20)
    financial_loss_prob: float      # 不当な金銭損失確率 (閾値 <= 0.15)
    smooth_resolution_prob: float   # 円滑合意確率 (閾値 >= 0.70)
    confidence: float               # AI確信度
    reason: str

@dataclass
class HybridJevReport:
    text: str
    overall_verdict: str       # PASS / REVIEW / FAIL
    action_lane: str           # AUTO_APPROVE / HUMAN_REVIEW / AUTO_REJECT
    draft_prefix: str          # [✅Jev自動承認済] / [⚠️要よっちゃん確認] / [🛑送信不可・自動差戻し]
    fast_failed: bool          # 第1層での早期打ち切り有無
    total_score: float         # 0.00 〜 1.00
    bool_audit: Dict[str, Any]
    scale_audit: Dict[str, Any]
    prob_audit: Dict[str, Any]
    summary_feedback: str

# ==============================================================================
# 2. 各層のJev評価エンジン
# ==============================================================================

def audit_boolean(text: str) -> BoolAuditResult:
    """第1層: 二値・ブール値ゲート（足切り門番）"""
    has_apology = any(w in text for w in ["お詫び", "申し訳", "ご不便", "恐縮"])
    no_careless_promise = not any(w in text for w in ["全額こちらで負担", "すべて無償で対応", "費用は全額持ちます"])
    has_action = any(w in text for w in ["元栓", "止水栓", "閉め", "写真", "訪問", "確認", "日程", "伺い"])

    passed = has_apology and no_careless_promise and has_action

    reasons = []
    if not has_apology:
        reasons.append("冒頭のお詫び・生活への配慮が欠落")
    if not no_careless_promise:
        reasons.append("原因確認前の安易な全額負担・無償確約を検知")
    if not has_action:
        reasons.append("具体的な行動指示または日程打診が不足")

    reason_str = "全必須チェック通過" if passed else " / ".join(reasons)
    return BoolAuditResult(passed, has_apology, no_careless_promise, has_action, reason_str)


def audit_scale(text: str) -> ScaleAuditResult:
    """第2層: 5段階スケール ＆ 定性ランク評価"""
    if "深くお詫び" in text or ("ご不便をおかけし" in text and "お詫び" in text):
        empathy = 5 if "深くお詫び" in text else 4
    elif "申し訳" in text or "ご不便" in text:
        empathy = 3
    else:
        empathy = 1

    if "原因を確認" in text and "協議" in text:
        risk = 5
    elif "原因を確認" in text or "協議" in text or "確認の上" in text:
        risk = 3
    elif "確認" in text:
        risk = 2
    else:
        risk = 1

    if ("時" in text or "候補" in text) and ("元栓" in text or "止水栓" in text):
        action = 5
    elif "元栓" in text or "止水栓" in text or "時" in text or "午前" in text or "午後" in text:
        action = 3
    else:
        action = 1

    avg = round((empathy + risk + action) / 3.0, 2)

    # 足切りルール: 全項目3以上 かつ 平均点によるランク分け
    if empathy >= 3 and risk >= 3 and action >= 3:
        if avg >= 4.5:
            grade = "S"
            passed = True
        elif avg >= 4.0:
            grade = "A"
            passed = True
        else:
            grade = "B"
            passed = True
    else:
        grade = "C"
        passed = False

    reason_str = f"ランク{grade}（平均 {avg} 点）: " + (
        "全項目3以上かつ高水準。" if grade in ("S", "A")
        else ("全項目3以上（標準水準・要確認推奨）。" if grade == "B" else "項目別の足切り基準（全項目3以上）を満たしていません。")
    )
    return ScaleAuditResult(passed, False, empathy, risk, action, avg, grade, reason_str)


def audit_probability(text: str, bool_res: BoolAuditResult, scale_res: ScaleAuditResult) -> ProbAuditResult:
    """第3層: 確率・不確実性（リスク・合意予測）"""
    if not bool_res.has_cause_investigation:
        financial_loss = 0.85
    elif scale_res.risk_control_level >= 4:
        financial_loss = 0.02
    elif scale_res.risk_control_level == 3:
        financial_loss = 0.12
    else:
        financial_loss = 0.35

    if scale_res.empathy_level <= 2:
        trouble_prob = 0.40
    elif scale_res.empathy_level == 3:
        trouble_prob = 0.18
    else:
        trouble_prob = 0.05

    if scale_res.action_clarity_level >= 4:
        smooth_prob = 0.92
    elif scale_res.action_clarity_level == 3:
        smooth_prob = 0.68
    else:
        smooth_prob = 0.40

    confidence = 0.94 if scale_res.grade in ("S", "A") else 0.85

    # 厳格PASS閾値（AUTO_APPROVE基準）
    passed = (trouble_prob <= 0.20) and (financial_loss <= 0.15) and (smooth_prob >= 0.70)
    if passed:
        reason_str = "リスク確率が安全閾値内（炎上<=20%, 損失<=15%, 合意>=70%）"
    elif trouble_prob <= 0.30 and financial_loss <= 0.30:
        reason_str = f"中程度リスク・合意率やや不足（炎上: {int(trouble_prob*100)}%, 損失: {int(financial_loss*100)}%, 合意: {int(smooth_prob*100)}%）"
    else:
        reason_str = f"危険リスク超過（炎上: {int(trouble_prob*100)}%, 損失: {int(financial_loss*100)}%）"

    return ProbAuditResult(passed, False, trouble_prob, financial_loss, smooth_prob, confidence, reason_str)

# ==============================================================================
# 3. 統合ハイブリッド監査パイプライン（早期打ち切り Fast-Fail ＆ 3レーン仕分け）
# ==============================================================================

def run_hybrid_jev_audit(text: str, fast_fail: bool = True) -> HybridJevReport:
    # --- 第1層: 二値門番 ---
    bool_res = audit_boolean(text)

    # 早期打ち切り（Fast-Fail）発動時: 第2層・第3層をスキップして即時 AUTO_REJECT
    if fast_fail and not bool_res.passed:
        scale_res = ScaleAuditResult(
            passed=False,
            skipped=True,
            empathy_level=0,
            risk_control_level=0,
            action_clarity_level=0,
            average_score=0.0,
            grade="SKIPPED",
            reason="第1層（二値ゲート）不合格のため早期打ち切り（推論スキップ）"
        )
        prob_res = ProbAuditResult(
            passed=False,
            skipped=True,
            trouble_escalation_prob=0.50 if not bool_res.has_apology else 0.25,
            financial_loss_prob=0.85 if not bool_res.has_cause_investigation else 0.20,
            smooth_resolution_prob=0.30,
            confidence=0.98,
            reason="第1層（二値ゲート）不合格のため早期打ち切り（推論スキップ）"
        )
        verdict = "FAIL"
        action_lane = "AUTO_REJECT"
        draft_prefix = "[🛑送信不可・自動差戻し]"
        score = 0.05
        feedback = (
            f"【総合判定: {verdict} / レーン: {action_lane} / スコア: {score}】\n"
            f"・⚡ 早期打ち切り (Fast-Fail): 発動（第2・第3層をスキップ）\n"
            f"・二値判定: 不合格 ({bool_res.reason})\n"
            f"・推奨アクション: {draft_prefix} 必須項目を補完して再生成してください。"
        )
        return HybridJevReport(
            text=text,
            overall_verdict=verdict,
            action_lane=action_lane,
            draft_prefix=draft_prefix,
            fast_failed=True,
            total_score=score,
            bool_audit=asdict(bool_res),
            scale_audit=asdict(scale_res),
            prob_audit=asdict(prob_res),
            summary_feedback=feedback
        )

    # --- 第2層: 段階スケール評価 ---
    scale_res = audit_scale(text)

    # --- 第3層: 確率・確信度評価 ---
    prob_res = audit_probability(text, bool_res, scale_res)

    # --- 3レーン自動仕分け（Autonomy Slider） ---
    if (
        bool_res.passed
        and scale_res.passed
        and scale_res.grade in ("S", "A")
        and prob_res.passed
        and prob_res.confidence >= 0.90
    ):
        verdict = "PASS"
        action_lane = "AUTO_APPROVE"
        draft_prefix = "[✅Jev自動承認済]"
    elif (
        bool_res.passed
        and scale_res.grade in ("S", "A", "B")
        and prob_res.trouble_escalation_prob <= 0.30
        and prob_res.financial_loss_prob <= 0.30
    ):
        verdict = "PASS"
        action_lane = "HUMAN_REVIEW"
        draft_prefix = "[⚠️要よっちゃん確認]"
    else:
        verdict = "FAIL"
        action_lane = "AUTO_REJECT"
        draft_prefix = "[🛑送信不可・自動差戻し]"

    # 総合スコア（加重平均）
    score = (
        (scale_res.average_score / 5.0) * 0.50 +
        prob_res.smooth_resolution_prob * 0.30 +
        (1.0 if bool_res.passed else 0.0) * 0.20
    ) - (prob_res.trouble_escalation_prob * 0.20 + prob_res.financial_loss_prob * 0.20)
    score = round(max(min(score, 1.0), 0.0), 2)

    feedback = (
        f"【総合判定: {verdict} / レーン: {action_lane} ({draft_prefix}) / スコア: {score}】\n"
        f"・二値判定: {'合格' if bool_res.passed else '不合格'} ({bool_res.reason})\n"
        f"・段階判定: ランク{scale_res.grade} ({scale_res.reason})\n"
        f"・確率判定: {'合格' if prob_res.passed else '要注意/不合格'} ({prob_res.reason})"
    )

    return HybridJevReport(
        text=text,
        overall_verdict=verdict,
        action_lane=action_lane,
        draft_prefix=draft_prefix,
        fast_failed=False,
        total_score=score,
        bool_audit=asdict(bool_res),
        scale_audit=asdict(scale_res),
        prob_audit=asdict(prob_res),
        summary_feedback=feedback
    )

# ==============================================================================
# 4. Obsidian 連携 (Markdown レポート保存 ＆ ダッシュボード更新)
# ==============================================================================

def save_audit_report(report: HybridJevReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    filename = f"Hybrid_Audit_{timestamp}.md"
    file_path = REPORTS_DIR / filename

    # 1. 06_Reports用 Markdown生成（Jev_Audit_Dashboard.py 連携キーも含む）
    md_content = f"""---
title: "Hybrid Jev Audit {timestamp}"
date: {now_str}
type: eval_report
category: hybrid_jev
status: {report.overall_verdict}
action_lane: {report.action_lane}
draft_prefix: "{report.draft_prefix}"
fast_failed: {str(report.fast_failed).lower()}
attempts: 1
score: {report.total_score}
eval_type: hybrid_jev
verdict: {report.overall_verdict}
total_score: {report.total_score}
bool_pass: {str(report.bool_audit['passed']).lower()}
scale_grade: "{report.scale_audit['grade']}"
scale_avg: {report.scale_audit['average_score']}
trouble_prob: {report.prob_audit['trouble_escalation_prob']}
financial_loss_prob: {report.prob_audit['financial_loss_prob']}
smooth_prob: {report.prob_audit['smooth_resolution_prob']}
created_at: "{now_str}"
---

# ハイブリッドJev監査レポート ({timestamp})

## 1. 総合評価サマリー
- **最終判定**: `{report.overall_verdict}`
- **仕分けレーン**: `{report.action_lane}` (`{report.draft_prefix}`)
- **早期打ち切り (Fast-Fail)**: `{report.fast_failed}`
- **総合スコア**: `{report.total_score}` / 1.00
- **監査結果**:
  - 二値判定: `{'PASS' if report.bool_audit['passed'] else 'FAIL'}` ({report.bool_audit['reason']})
  - 段階判定: `ランク {report.scale_audit['grade']}` ({report.scale_audit['average_score']}点)
  - 確率判定: 炎上リスク `{int(report.prob_audit['trouble_escalation_prob']*100)}%` / 損失リスク `{int(report.prob_audit['financial_loss_prob']*100)}%`

## 2. 監査対象テキスト
> {report.text}

## 3. レビュー詳細
```json
{json.dumps(asdict(report), indent=2, ensure_ascii=False)}
```
"""
    file_path.write_text(md_content, encoding="utf-8")
    print(f"[Obsidian連携] レポートを保存しました: {file_path}")
    return file_path


# ==============================================================================
# 5. 実行部
# ==============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-lanes":
        samples = [
            (
                "① 完全自動承認 (AUTO_APPROVE)",
                "水漏れでご不便をおかけし深くお詫び申し上げます。生活への影響を最小限にするため、"
                "まず元栓を閉め、被害状況の写真撮影をお願いいたします。現地にて原因を確認した上で"
                "費用や修繕方針を協議させてください。明日10時または14時でご訪問可能ですがご都合いかがでしょうか。"
            ),
            (
                "② 人間レビュー待ち (HUMAN_REVIEW / ランクB・中間リスク)",
                "水漏れの件、申し訳ございません。まずは止水栓を閉めてお待ちください。"
                "現地で状況を確認の上で対応いたしますので、明日の午後に伺います。"
            ),
            (
                "③ 自動差戻し・早期打ち切り (AUTO_REJECT / Fast-Fail)",
                "水漏れですね。明日業者を行かせます。費用は全額こちらで負担します。"
            ),
        ]
        for label, sample_text in samples:
            print(f"\n=== {label} ===")
            rep = run_hybrid_jev_audit(sample_text, fast_fail=True)
            print(json.dumps(asdict(rep), indent=2, ensure_ascii=False))
        sys.exit(0)

    test_text = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "水漏れでご不便をおかけし深くお詫び申し上げます。生活への影響を最小限にするため、"
             "まず元栓を閉め、被害状況の写真撮影をお願いいたします。現地にて原因を確認した上で"
             "費用や修繕方針を協議させてください。明日10時または14時でご訪問可能ですがご都合いかがでしょうか。"
    )

    report = run_hybrid_jev_audit(test_text, fast_fail=True)
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    save_audit_report(report)

    try:
        from Jev_Audit_Dashboard import build_dashboard
        build_dashboard()
    except ImportError:
        pass
