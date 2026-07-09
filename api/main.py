from fastapi import FastAPI
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from api.schemas import Transaction, PredictionResponse
from api.predictor import predict_fraud
from api.rules_engine import check_rules
from api.rag_engine import retrieve_similar_cases
from api.llm_analyst import generate_investigation_report
from api.history_engine import save_search, get_history

app = FastAPI(title="Fraud Detection API", version="1.0")

@app.get("/")
def root():
    return {"status": "Fraud Detection API is running"}

@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: Transaction):
    result = predict_fraud(transaction.dict())
    return result

@app.post("/investigate")
def investigate(transaction: Transaction):
    txn_dict = transaction.dict()

    ml_result = predict_fraud(txn_dict)
    rule_flags = check_rules(txn_dict)
    similar_cases = retrieve_similar_cases(txn_dict, rule_flags)

    narrative = generate_investigation_report(
        txn_dict,
        ml_result["fraud_probability"],
        rule_flags,
        ml_result["top_features"],
        similar_cases
    )

    # Parse the LLM's verdict line, fall back to model-based tier if parsing fails
    final_risk_tier = ml_result["risk_tier"]
    narrative_body = narrative
    if narrative.startswith("VERDICT:"):
        first_line, _, rest = narrative.partition("\n")
        verdict = first_line.replace("VERDICT:", "").strip()
        if verdict in ["Low", "Medium", "High"]:
            final_risk_tier = verdict
        narrative_body = rest.strip()

    result = {
        "transaction": txn_dict,
        "fraud_probability": ml_result["fraud_probability"],
        "model_risk_tier": ml_result["risk_tier"],
        "risk_tier": final_risk_tier,
        "top_features": ml_result["top_features"],
        "rule_flags": rule_flags,
        "similar_cases": [{"section": c["section"], "similarity": round(c["similarity"], 3)} for c in similar_cases],
        "llm_narrative": narrative_body
    }

    save_search(
        transaction=txn_dict,
        fraud_probability=ml_result["fraud_probability"],
        risk_tier=final_risk_tier,
        top_features=ml_result["top_features"],
        rule_flags=rule_flags,
        similar_cases=similar_cases,
        llm_narrative=narrative_body
    )

    return result

@app.get("/history")
def history(limit: int = 50):
    return get_history(limit)
