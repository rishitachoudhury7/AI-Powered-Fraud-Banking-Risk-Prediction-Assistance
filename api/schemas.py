from pydantic import BaseModel

class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

class PredictionResponse(BaseModel):
    prediction: int
    fraud_probability: float
    risk_tier: str
    top_features: list[dict]
