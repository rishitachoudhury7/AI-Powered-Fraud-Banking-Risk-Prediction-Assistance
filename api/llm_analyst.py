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
- top_features (SHAP values showing which encoded features pushed the model toward or away from fraud — positive impact means it pushed toward fraud, negative means it pushed toward legitimate)
- rule_flags (rule-based red flags triggered)

Your job:
1. State a risk verdict (Low / Medium / High) based on the probability, SHAP evidence, and rule flags together.
2. Explain WHY in plain language, grounded ONLY in the provided SHAP features and rule flags. Never invent reasons not present in the data.
3. If the SHAP evidence and rule flags disagree with the model's raw probability, point that out explicitly — this is valuable for a human analyst reviewing the case.
4. Note if this resembles a known AML pattern (e.g. mule account, account takeover, structuring) — only if the evidence supports it.
5. Recommend one action: Approve / Escalate to human analyst / Block.

Be concise (under 180 words) and audit-friendly. No speculation beyond the data given."""

def generate_investigation_report(transaction: dict, probability: float, rule_flags: list, top_features: list) -> str:
    evidence = {
        "transaction": transaction,
        "fraud_probability": round(probability, 4),
        "top_features": top_features,
        "rule_flags": rule_flags
    }

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(evidence)}
        ]
    )

    return response.choices[0].message.content
