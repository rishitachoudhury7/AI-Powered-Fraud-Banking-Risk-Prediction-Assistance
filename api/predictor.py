import joblib
import pandas as pd
import shap

pipeline = joblib.load("fraud_model.pkl")
preprocessor = pipeline.named_steps["preprocessor"]
xgb_model = pipeline.named_steps["model"]

explainer = shap.TreeExplainer(xgb_model)

def predict_fraud(transaction: dict) -> dict:
    amount = transaction["amount"]
    oldbalanceOrg = transaction["oldbalanceOrg"]
    newbalanceOrig = transaction["newbalanceOrig"]
    oldbalanceDest = transaction["oldbalanceDest"]
    newbalanceDest = transaction["newbalanceDest"]

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

    prediction = int(pipeline.predict(input_data)[0])
    probability = float(pipeline.predict_proba(input_data)[0][1])

    if probability >= 0.8:
        risk_tier = "High"
    elif probability >= 0.4:
        risk_tier = "Medium"
    else:
        risk_tier = "Low"

    input_processed = preprocessor.transform(input_data)
    feature_names = preprocessor.get_feature_names_out()

    shap_values = explainer.shap_values(input_processed)

    feature_impact = sorted(
        zip(feature_names, shap_values[0]),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]

    top_features = [
        {"feature": f, "impact": round(float(v), 4)} for f, v in feature_impact
    ]

    return {
        "prediction": prediction,
        "fraud_probability": probability,
        "risk_tier": risk_tier,
        "top_features": top_features
    }
