import joblib
import pandas as pd

model = joblib.load("fraud_model.pkl")

def predict_fraud(transaction: dict) -> dict:
    amount = transaction["amount"]
    oldbalanceOrg = transaction["oldbalanceOrg"]
    newbalanceOrig = transaction["newbalanceOrig"]
    oldbalanceDest = transaction["oldbalanceDest"]
    newbalanceDest = transaction["newbalanceDest"]

    # Same feature engineering as your Streamlit app
    diffsender = newbalanceOrig - (oldbalanceOrg - amount)
    diffreceiver = newbalanceDest - (oldbalanceDest + amount)

    input_data = pd.DataFrame({
        "step": [transaction["step"]],
        "type": [transaction["type"]],
        "amount": [amount],
        "oldbalanceOrg": [oldbalanceOrg],
        "newbalanceOrig": [newbalanceOrig],
        "oldbalanceDest": [oldbalanceDest],
        "newbalanceDest": [newbalanceDest],
        "diffsender": [diffsender],
        "diffreceiver": [diffreceiver]
    })

    prediction = int(model.predict(input_data)[0])
    probability = float(model.predict_proba(input_data)[0][1])

    if probability >= 0.8:
        risk_tier = "High"
    elif probability >= 0.4:
        risk_tier = "Medium"
    else:
        risk_tier = "Low"

    return {
        "prediction": prediction,
        "fraud_probability": probability,
        "risk_tier": risk_tier
    }
