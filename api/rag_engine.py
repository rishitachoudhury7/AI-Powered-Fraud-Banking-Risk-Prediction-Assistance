import os
import requests
from supabase import create_client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path, override=True)

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HF_HEADERS = {"Authorization": f"Bearer {os.environ['HF_API_TOKEN']}"}

def get_embedding(text: str) -> list[float]:
    response = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={"inputs": text, "options": {"wait_for_model": True}}
    )
    response.raise_for_status()
    return response.json()

def build_query_text(transaction: dict, rule_flags: list) -> str:
    """Turn a transaction + its rule flags into a natural-language query for retrieval."""
    parts = [
        f"Transaction type: {transaction['type']}, amount: {transaction['amount']}.",
        f"Origin balance went from {transaction['oldbalanceOrg']} to {transaction['newbalanceOrig']}.",
        f"Destination balance went from {transaction['oldbalanceDest']} to {transaction['newbalanceDest']}."
    ]
    if rule_flags:
        parts.append("Red flags: " + "; ".join(rule_flags) + ".")
    return " ".join(parts)

def retrieve_similar_cases(transaction: dict, rule_flags: list, top_k: int = 2) -> list[dict]:
    query_text = build_query_text(transaction, rule_flags)
    query_embedding = get_embedding(query_text)

    response = supabase.rpc(
        "match_policy_chunks",
        {"query_embedding": query_embedding, "match_count": top_k}
    ).execute()

    return response.data
