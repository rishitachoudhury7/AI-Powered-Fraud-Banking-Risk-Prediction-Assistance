import os
import json
from groq import Groq
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path, override=True)

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are a Banking Fraud & AML Compliance Analyst Assistant.

You will be given a JSON object containing:
- transaction details (type, amount, balances)
- fraud_probability (from an ML model)
- top_features (SHAP values showing which encoded features pushed the model toward or away from fraud)
- rule_flags (rule-based red flags triggered)
- similar_cases (historical fraud case studies retrieved as the closest precedent matches, each with a similarity score)

Your job:
1. State a risk verdict (Low / Medium / High) based on the probability, SHAP evidence, rule flags, and similar historical cases together.
2. Explain WHY in plain language, grounded ONLY in the provided evidence. Never invent reasons not present in the data.
3. If a similar historical case is relevant, reference it explicitly by name (e.g. "This closely resembles Case 003...") and note what happened in that case.
4. If the SHAP evidence, rule flags, and model probability disagree with each other, point that out explicitly.
5. Note if this resembles a known AML pattern — only if the evidence supports it.
6. Recommend one action: Approve / Escalate to human analyst / Block.

Be concise (under 200 words) and audit-friendly. No speculation beyond the data given."""

def generate_investigation_report(transaction: dict, probability: float, rule_flags: list, top_features: list, similar_cases: list) -> str:
    evidence = {
        "transaction": transaction,
        "fraud_probability": round(probability, 4),
        "top_features": top_features,
        "rule_flags": rule_flags,
        "similar_cases": [
            {"section": c["section"], "similarity": round(c["similarity"], 3), "summary": c["content"][:400]}
            for c in similar_cases
        ]
    }

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(evidence)}
        ]
    )

    return response.choices[0].message.content
