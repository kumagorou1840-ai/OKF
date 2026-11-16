import json
from pydantic import BaseModel, Field
import ollama
from schemas import ContractSchema

class JevAuditResult(BaseModel):
    status: str = Field(..., pattern="^(PASS|FAIL)$")
    binary_check: bool
    scale_score: int = Field(..., ge=1, le=5)
    confidence_prob: float = Field(..., ge=0.0, le=1.0)
    feedback: str

def evaluate_with_jev(contract: ContractSchema) -> JevAuditResult:
    reasons = []
    binary_ok = True
    if contract.rent_diff != 0 and (not contract.memo or contract.memo == "特になし"):
        binary_ok = False
        reasons.append(f"賃料が {contract.rent_diff:+,}円 変動していますが、memoが「{contract.memo}」です。具体的な改定理由をmemoに記載してください。")

    change_ratio = abs(contract.rent_diff) / contract.current_rent if contract.current_rent > 0 else 0
    if change_ratio <= 0.05:
        scale_score = 5
    elif change_ratio <= 0.10:
        scale_score = 4
    elif change_ratio <= 0.20:
        scale_score = 3
        if contract.flag == "ACTIVE":
            reasons.append("賃料改定幅が10%を超えています。flagを 'REVIEW_REQUIRED' に変更してください。")
    else:
        scale_score = 2
        if contract.flag != "URGENT":
            reasons.append(f"賃料改定率が {change_ratio:.1%} と高いため、flagを 'URGENT' にしてください。")

    prompt = f"""
以下の契約JSONデータを監査し、JSON形式で評価を返してください。
{contract.model_dump_json(indent=2)}
出力キー: "confidence_prob" (0.0〜1.0), "llm_comment" (1文で簡潔に)
"""
    try:
        response = ollama.chat(model="gemma4:26b", messages=[{"role": "user", "content": prompt}], format="json")
        llm_eval = json.loads(response["message"]["content"])
        prob = float(llm_eval.get("confidence_prob", 0.85))
        if prob < 0.8:
            reasons.append(f"LLM監査指摘: {llm_eval.get('llm_comment', '')}")
    except Exception:
        prob = 0.85 if binary_ok and scale_score >= 3 else 0.50

    is_pass = binary_ok and (scale_score >= 3 or contract.flag == "URGENT") and (prob >= 0.8) and (len(reasons) == 0)

    return JevAuditResult(
        status="PASS" if is_pass else "FAIL",
        binary_check=binary_ok,
        scale_score=scale_score,
        confidence_prob=prob,
        feedback="Jev監査クリア（承認）" if is_pass else " / ".join(reasons)
    )
