from pydantic import BaseModel
from typing import Optional

class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

    # New fields for cycle detection and richer context
    timestamp: Optional[str] = None
    nameOrig: Optional[str] = None
    origin_bank: Optional[str] = None
    nameDest: Optional[str] = None
    dest_bank: Optional[str] = None
    amount_received: Optional[float] = None
    receiving_currency: Optional[str] = None
    payment_currency: Optional[str] = None
    payment_format: Optional[str] = None
    account_age_days: Optional[int] = None

class TransactionChain(BaseModel):
    transactions: list[Transaction]

class PredictionResponse(BaseModel):
    prediction: int
    fraud_probability: float
    risk_tier: str
    top_features: list[dict]
