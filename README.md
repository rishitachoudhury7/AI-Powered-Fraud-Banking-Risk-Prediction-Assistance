# Fraud Detection App

An XGBoost-based fraud detection system trained on 6.3M+ financial transactions, deployed as an interactive Streamlit app for real-time fraud risk scoring.

🔗 **Live app:** [[frauddetection-wkqeksfyxo2msylcficcwj.streamlit.app](https://frauddetection-wkqeksfyxo2msylcficcwj.streamlit.app/)](https://rishitachoudhury7-fraud-detection-dashboard-hqxcnk.streamlit.app/)

---

## Overview

This project detects fraudulent financial transactions in a highly imbalanced dataset — only **0.13%** of transactions (8,213 out of 6,362,620) are fraudulent. Rather than optimizing for accuracy (a misleading metric on imbalanced data — predicting "no fraud" for every transaction would already score ~99.87%), the model is evaluated and tuned on **PR-AUC** and **precision/recall on the minority class**, giving an honest measure of fraud-catching performance.

The final pipeline achieves a **PR-AUC of 0.9683**, and after threshold optimization, catches **87% of fraud cases at 97% precision** — meaning very few false alarms for every fraud caught.

## Dataset

- **Source:** Synthetic financial transactions dataset (PaySim-style), ~6.36M rows
- **Target:** `isFraud` (1 = fraudulent, 0 = legitimate)
- **Key features:** `step` (time unit), `type` (transaction type), `amount`, sender/receiver balances before and after the transaction
- **Class imbalance:** 0.13% fraud rate

### Exploratory Data Analysis

- Fraud occurs **exclusively** in `TRANSFER` and `CASH_OUT` transaction types — `CASH_IN`, `DEBIT`, and `PAYMENT` transactions show zero fraud in this dataset.
- Fraudulent transactions are not uniformly distributed over time (`step`), suggesting bursty fraud patterns.
- Engineered two anomaly features:
  - `diffsender` = `oldbalanceOrg` − `newbalanceOrig`
  - `diffreceiver` = `oldbalanceDest` − `newbalanceDest`
  
  These flag inconsistencies in account balances around a transaction, though on their own they showed only a weak relationship with fraud — useful as model inputs rather than standalone rules.

## Modeling Approach

| Step | Approach |
|---|---|
| Preprocessing | One-hot encoding for `type`, standard scaling for numerical features (via `ColumnTransformer`) |
| Baseline | Logistic Regression with SMOTE oversampling — high recall but very low precision (98% false positive rate on flagged fraud) |
| Final model | **XGBoost Classifier** with `scale_pos_weight` to handle class imbalance natively (no SMOTE needed) |
| Threshold tuning | Precision-recall curve analysis to find the F1-optimal decision threshold (0.994, vs. the default 0.5) |

### Why XGBoost over Logistic Regression + SMOTE

The baseline model (Logistic Regression + SMOTE) recovered 95% of fraud cases but at the cost of ~63,000 false positives — a precision of just 2%, which would overwhelm any real fraud review team. Switching to XGBoost with `scale_pos_weight` and tuning the classification threshold on the precision-recall curve dramatically improved precision while keeping recall high.

### Final Model Performance (test set, 1.27M transactions)

| Metric | Score |
|---|---|
| PR-AUC | 0.9683 |
| Precision (fraud class) | 0.97 |
| Recall (fraud class) | 0.87 |
| F1-score (fraud class) | 0.92 |

Confusion matrix at the optimized threshold:

|  | Predicted: Legit | Predicted: Fraud |
|---|---|---|
| **Actual: Legit** | 1,270,853 | 51 |
| **Actual: Fraud** | 206 | 1,414 |

Out of 1,620 fraudulent transactions in the test set, the model correctly flags 1,414 — with only 51 false alarms across 1.27M legitimate transactions.

## Tech Stack

- **Modeling:** Python, scikit-learn, XGBoost, imbalanced-learn (SMOTE for baseline comparison)
- **App:** Streamlit
- **Serialization:** joblib
- **Deployment:** Streamlit Community Cloud

## Project Structure

```
├── Fraud_detection.ipynb   # EDA, feature engineering, model training & evaluation
├── app.py                  # Streamlit app for real-time predictions
├── fraud_detection.py      # Supporting model/pipeline code
├── fraud_model.pkl         # Trained XGBoost pipeline (preprocessing + model)
├── requirements.txt        # Dependencies
└── README.md
```

## Running Locally

```bash
git clone https://github.com/rishitachoudhury7/Fraud_detection.git
cd Fraud_detection
pip install -r requirements.txt
streamlit run app.py
```

The app takes transaction details as input (step, type, amount, sender/receiver balances) and returns a fraud prediction along with the model's probability score.

"My model correctly identifies large origin balances as a risk signal, but under-weights cases where destination accounts show non-zero pre-existing balances — a known blind spot without account-level historical features." 

## Future Work

- Redeploy on AWS for more control over scaling and latency
- Build a React/Next.js frontend (deployed on Vercel) for a more polished user experience
- Add SHAP-based explainability so flagged transactions come with a reason, not just a score
- Explore graph-based features (e.g. via NetworkX) to catch coordinated fraud rings rather than single transactions in isolation
-incorporating account-level transaction history / graph features would likely improve detection of multi-hop fraud patterns like TRANSFER→CASH_OUT chains
## Author

**Rishita Choudhury**
[GitHub](https://github.com/rishitachoudhury7) · [LinkedIn](https://www.linkedin.com/in/rishitachoudhury-41358a290)
