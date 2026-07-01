from fastapi import FastAPI
import sys
import os

# Ensure the repo root is on the path so we can import fraud_model.pkl correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from api.schemas import Transaction, PredictionResponse
from api.predictor import predict_fraud

app = FastAPI(title="Fraud Detection API", version="1.0")

@app.get("/")
def root():
    return {"status": "Fraud Detection API is running"}

@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: Transaction):
    result = predict_fraud(transaction.dict())
    return result
