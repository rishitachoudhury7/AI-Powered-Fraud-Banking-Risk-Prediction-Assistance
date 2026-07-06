import os
from sentence_transformers import SentenceTransformer
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
model = SentenceTransformer("all-MiniLM-L6-v2")

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
    query_embedding = model.encode(query_text).tolist()

    response = supabase.rpc(
        "match_policy_chunks",
        {"query_embedding": query_embedding, "match_count": top_k}
    ).execute()

    return response.data
