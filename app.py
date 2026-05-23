
import streamlit as st
import pandas as pd
import joblib

# Load model
model = joblib.load('fraud_model.pkl')

st.title("Fraud Detection App")

st.write("Enter transaction details:")

# User Inputs
step = st.number_input("Step", min_value=0)

transaction_type = st.selectbox(
    "Transaction Type",
    ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
)

amount = st.number_input("Amount", min_value=0.0)

oldbalanceOrg = st.number_input("Old Balance Origin", min_value=0.0)

newbalanceOrig = st.number_input("New Balance Origin", min_value=0.0)

oldbalanceDest = st.number_input("Old Balance Destination", min_value=0.0)

newbalanceDest = st.number_input("New Balance Destination", min_value=0.0)

# Feature engineering
diffsender = newbalanceOrig - (oldbalanceOrg - amount)

diffreceiver = newbalanceDest - (oldbalanceDest + amount)

# Prediction button
if st.button("Predict Fraud"):

    input_data = pd.DataFrame({
        'step': [step],
        'type': [transaction_type],
        'amount': [amount],
        'oldbalanceOrg': [oldbalanceOrg],
        'newbalanceOrig': [newbalanceOrig],
        'oldbalanceDest': [oldbalanceDest],
        'newbalanceDest': [newbalanceDest],
        'diffsender': [diffsender],
        'diffreceiver': [diffreceiver]
    })

    prediction = model.predict(input_data)[0]

    probability = model.predict_proba(input_data)[0][1]

    if prediction == 1:
        st.error(f"Fraud Detected! Probability: {probability:.2f}")
    else:
        st.success(f"Legitimate Transaction. Probability: {probability:.2f}")
