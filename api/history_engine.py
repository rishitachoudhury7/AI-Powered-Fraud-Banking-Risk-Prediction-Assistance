import os
from supabase import create_client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path, override=True)

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def save_search(transaction: dict, fraud_probability: float, risk_tier: str,
                top_features: list, rule_flags: list, similar_cases: list, llm_narrative: str):
    supabase.table("search_history").insert({
        "transaction": transaction,
        "fraud_probability": fraud_probability,
        "risk_tier": risk_tier,
        "top_features": top_features,
        "rule_flags": rule_flags,
        "similar_cases": [
            {"section": c["section"], "similarity": c["similarity"]} for c in similar_cases
        ],
        "llm_narrative": llm_narrative
    }).execute()

def get_history(limit: int = 50) -> list[dict]:
    response = (
        supabase.table("search_history")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data
