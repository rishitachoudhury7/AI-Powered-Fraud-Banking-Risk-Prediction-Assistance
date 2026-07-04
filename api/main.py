from fastapi import FastAPI
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from api.schemas import Transaction, PredictionResponse
from api.predictor import predict_fraud
from api.rules_engine import check_rules
from api.llm_analyst import generate_investigation_report

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

    narrative = generate_investigation_report(
        txn_dict,
        ml_result["fraud_probability"],
        rule_flags,
        ml_result["top_features"]
    )

    return {
        "transaction": txn_dict,
        "fraud_probability": ml_result["fraud_probability"],
        "risk_tier": ml_result["risk_tier"],
        "top_features": ml_result["top_features"],
        "rule_flags": rule_flags,
        "llm_narrative": narrative
    }
