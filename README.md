# AI Fraud Investigation & Banking Risk Compliance Assistant

An end-to-end fraud investigation copilot that combines a production XGBoost classifier, SHAP explainability, a rule-based AML typology engine, retrieval-augmented generation (RAG) over historical case precedent, and an LLM compliance analyst — wrapped in a live dashboard for single-transaction and multi-hop chain investigations.

**🔗 Live Demo:** https://rishitachoudhury7-fraud-detection-dashboard-hqxcnk.streamlit.app/ 

> The backend runs on Render's free tier and may take 2–3 mins to respond on the first request after a period of inactivity (cold start).

---

## What this project does

Given a transaction (or a sequence of linked transactions), the system returns:
- A fraud probability from a trained XGBoost model
- A per-transaction SHAP explanation (which features drove the score, and in which direction)
- Rule-based AML red flags (account draining, mule-account indicators, high-value thresholds, credential-change proximity, velocity)
- The most similar historical fraud case studies, retrieved via vector search
- A synthesized risk verdict and recommended action from an LLM compliance analyst, grounded explicitly in the evidence above — not free-floating LLM judgment

For chains of linked transactions, it additionally detects patterns invisible to single-transaction scoring: mule pass-through (TRANSFER → CASH_OUT), structuring, round-trip laundering cycles (A → B → A), and cross-currency layering.

---

## Architecture

```
Transaction(s)
     │
     ▼
XGBoost Pipeline (preprocessing + classifier) ──► fraud probability, model-only risk tier
     │
     ▼
SHAP TreeExplainer ──► top feature attributions (direction + magnitude)
     │
     ▼
Rules Engine ──► explainable AML red flags (single-transaction + chain-level)
     │
     ▼
RAG Retrieval (Supabase pgvector + Hugging Face embeddings) ──► similar historical cases
     │
     ▼
Groq LLM (llama-3.3-70b-versatile) ──► synthesized verdict + narrative,
                                        explicitly reconciling model score vs. rule/RAG evidence
     │
     ▼
Streamlit Dashboard ──► single investigation, chain investigation, history, analytics
```

**Key design decision:** the final risk verdict shown to the user is the LLM's synthesized judgment, not the raw model probability alone. The dashboard displays both side by side — model-only tier and final verdict — so any disagreement between them is visible, not hidden. This reflects a real constraint in AML compliance: a low model score should never silently override multiple corroborating rule-based signals.

---

## Model

- **Algorithm:** XGBoost classifier inside a scikit-learn `Pipeline` (preprocessing + model), trained on 6.3M+ PaySim-style transactions
- **Performance:** PR-AUC 0.9698 on held-out test data
- **Class imbalance handling:** `scale_pos_weight`, tuned for the ~0.1% fraud rate in the training data
- **Explainability:** SHAP `TreeExplainer`, applied post-preprocessing so feature attributions map to the actual encoded features the model sees

**Known limitation:** the model scores each transaction independently and has no visibility into account history or linked transactions. This is a structural constraint of single-transaction classification, not a training deficiency — it's the reason the rules engine and chain investigation layer exist as complementary detection methods rather than afterthoughts. A confirmed real example: a labeled fraud transaction (TRANSFER → CASH_OUT mule pattern) scored under 8% model probability in isolation, while the rules engine correctly flagged it and the LLM correctly escalated it to High.

---

## Detection capabilities

**Single-transaction rules:**
- Full origin-account balance drain
- Transaction amount ≥98% of sender's balance
- Destination balance unchanged despite a transfer (mule indicator)
- High-value CASH_OUT/TRANSFER above threshold
- Transaction shortly after a credential/contact-detail change
- First-ever transaction of a given type for an account, combined with a recent credential change (early-stage account-takeover signal)

**Chain-level rules** (via `/investigate-chain`, applied across a sequence of linked transactions):
- Mule pass-through: TRANSFER immediately followed by CASH_OUT of a near-identical amount
- Structuring: multiple similar-sized transactions within a chain
- Cycle detection: A → B → A round-trips using account identity and timestamp matching, including detection of amount discrepancies (possible fee/conversion skimming) between the two legs
- Currency mismatch: payment currency ≠ receiving currency, a common cross-border layering signal
- Velocity: 3+ transactions from the same origin account within one chain (staged withdrawal pattern)

**Calibration note:** the system requires at least two corroborating rule flags (`strong_override`) before the LLM is permitted to escalate the final verdict above what the raw model probability alone would suggest — a single weak signal is not sufficient. This was added after an internal calibration pass identified over-escalation on ordinary transactions; a batch test against everyday, non-suspicious transactions confirmed the fix.

---

## RAG layer

Historical fraud case studies (composite, illustrative — not real customer data) are chunked, embedded via the Hugging Face Inference API (`sentence-transformers/all-MiniLM-L6-v2`), and stored in Supabase using the `pgvector` extension with cosine similarity search. At investigation time, the transaction and its triggered rule flags are embedded into a query and matched against the case library, and the top matches are passed to the LLM as grounding context — so the narrative can cite precedent by name (e.g., "This closely resembles Case 003...") rather than reasoning from general knowledge alone.

---

## Tech stack

| Layer | Technology |
|---|---|
| Model | XGBoost, scikit-learn Pipeline, SHAP |
| Backend API | FastAPI, Pydantic, Uvicorn |
| Rules engine | Pure Python, no external dependencies |
| Vector store | Supabase (PostgreSQL + pgvector) |
| Embeddings | Hugging Face Inference API (`all-MiniLM-L6-v2`) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| History storage | Supabase (`jsonb` columns) |
| Dashboard | Streamlit, Plotly |
| Backend hosting | Render (free tier) |
| Dashboard hosting | Streamlit Community Cloud |

---

## API endpoints

- `POST /predict` — raw model prediction + SHAP for a single transaction
- `POST /investigate` — full pipeline (model + rules + RAG + LLM) for a single transaction, saved to history
- `POST /investigate-chain` — full pipeline applied to a sequence of linked transactions, plus chain-level pattern detection and an overall verdict
- `GET /history` — retrieve past investigations
- `GET /docs` — interactive Swagger UI

---

## Dashboard

- **Dashboard** — KPI summary (total investigations, risk distribution, average fraud probability, rule hit rate), fraud probability trend, risk distribution chart
- **Investigate** — single-transaction form (including optional account ID, timestamp, currency, and credential-change metadata to enable richer rule checks), results shown as risk cards, SHAP chart, rule flags, similar cases, and full LLM narrative
- **Chain Investigation** — dynamically add/remove transaction hops, run a linked-chain investigation, view a chain summary (overall risk, hop count, risk trend across hops, chain-level flags) plus expandable per-hop detail
- **Investigation History** — searchable table with click-to-expand full case detail (transaction, balances, SHAP, rule flags, similar cases, narrative)
- **Settings** — system/model metadata

---

## Notable engineering decisions and debugging (selected)

- **Fair-lending consideration:** gender and nationality were deliberately excluded from both the model and the rules engine, despite being present in some source data formats, due to fair-lending/anti-discrimination risk in a real compliance context. Account age, transaction timing, and account identity were used instead as legitimate, non-protected risk signals.
- **RAG retrieval silently returning empty results:** traced through client-library, raw HTTP, and direct-SQL layers to isolate the cause to an `ivfflat` vector index configured with far more clusters (`lists=100`) than the dataset had rows (8) — a classic case of copy-pasted index tuning not being scaled to actual data volume. Fixed by dropping the index in favor of exact sequential scan, appropriate at this dataset's scale.
- **Free-tier memory constraint:** the original `sentence-transformers` (PyTorch-backed) embedding approach exceeded Render's 512MB free-tier limit. Replaced with calls to the Hugging Face-hosted Inference API, trading a small amount of per-request latency for a materially lighter deployment footprint — a deliberate, documented tradeoff rather than a workaround.
- **Model/rules/RAG disagreement:** rather than resolving disagreements between the raw model score, rule flags, and retrieved case evidence silently, the system surfaces them explicitly (`model_risk_tier` vs. final `risk_tier`, `strong_override` flag) so a human reviewer can see where the automated layers disagreed and why.

---

## Future work

- Account-level and graph-based features (transaction velocity, in/out-degree, account age) fed directly into the model rather than only the rules layer
- Formal link-analysis/graph algorithms for cycle and community detection beyond direct A→B→A matching
- Model calibration curve (predicted probability vs. observed fraud rate) to validate the 0.4/0.8 risk-tier thresholds against real distribution, not fixed cutoffs
- Retraining with account-level aggregate features to close the gap on multi-hop patterns the model currently misses in isolation

---

## Running locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload      # backend, http://127.0.0.1:8000/docs
streamlit run dashboard.py          # dashboard, http://localhost:8501
```

Requires a `.env` file (not committed) with `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, and `HF_API_TOKEN`.

---

## Disclaimer

This project uses synthetic/illustrative transaction data and composite case studies for educational and portfolio purposes. It is not connected to any real financial institution, does not process real customer data, and is not intended for production use in an actual compliance environment without substantial further validation.
