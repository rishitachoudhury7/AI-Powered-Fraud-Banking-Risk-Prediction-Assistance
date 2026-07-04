import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are a Banking Fraud & AML Compliance Analyst Assistant.

You will be given a JSON object containing:
- transaction details (type, amount, balances)
- fraud_probability (from an ML model)
- rule_flags (rule-based red flags triggered)

Your job:
1. State a risk verdict (Low / Medium / High) based on the probability and flags.
2. Explain WHY in plain language, grounded ONLY in the provided transaction data and rule flags. Never invent reasons not present in the data.
3. Note if this resembles a known AML pattern (e.g. mule account, account takeover, structuring) — only if the evidence supports it.
4. Recommend one action: Approve / Escalate to human analyst / Block.

Be concise (under 150 words) and audit-friendly. No speculation beyond the data given."""

def generate_investigation_report(transaction: dict, probability: float, rule_flags: list) -> str:
    evidence = {
        "transaction": transaction,
        "fraud_probability": round(probability, 4),
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
