import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import hashlib
from datetime import datetime

API_URL = "https://fraud-detection-zgeo.onrender.com"

st.set_page_config(page_title="AI Fraud Investigation & Compliance Assistant", layout="wide", initial_sidebar_state="expanded")

# ---------- DARK NAVY ENTERPRISE THEME ----------
st.markdown("""
<style>
.stApp { background-color: #0b1220; color: #e2e8f0; }
[data-testid="stSidebar"] { background-color: #070c17; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 15px; padding: 6px 0; }

h1, h2, h3, h4 { color: #f1f5f9 !important; }
p, span, label, div { color: #cbd5e1; }

.metric-card {
    background: linear-gradient(145deg, #111a2e, #0d1526);
    border-radius: 10px; padding: 18px 20px;
    border: 1px solid #1e293b;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.section-card {
    background: linear-gradient(145deg, #111a2e, #0d1526);
    border-radius: 10px; padding: 24px;
    border: 1px solid #1e293b;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    margin-bottom: 20px;
}
.result-card {
    background: #0d1526; border-radius: 10px; padding: 16px 18px;
    border: 1px solid #1e293b; text-align: center;
}
.result-card p.label { color: #64748b; font-size: 12px; margin: 0 0 6px 0; text-transform: uppercase; letter-spacing: 0.5px; }
.result-card p.value { font-size: 22px; font-weight: 700; margin: 0; }

.risk-bar-bg { background: #1e293b; border-radius: 6px; height: 10px; overflow: hidden; margin-top: 4px; }
.risk-bar-fill { height: 100%; border-radius: 6px; }

[data-testid="stDataFrame"] { background-color: #0d1526; }

.stButton button {
    background-color: #2563eb; color: white; border: none; font-weight: 600;
}
.stButton button:hover { background-color: #3b82f6; }

hr { border-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

RISK_COLORS = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
RISK_ACTION = {"High": "Escalate", "Medium": "Review", "Low": "Approve"}

if "chain_hops" not in st.session_state:
    st.session_state.chain_hops = [
        {"step": 1, "type": "TRANSFER", "amount": 0.0, "oldbalanceOrg": 0.0,
         "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0}
    ]

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🛡️ AI Fraud Investigation\n**& Compliance Assistant**")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🔎 Investigate", "🔗 Chain Investigation", "📚 Investigation History", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("XGBoost · SHAP · Rules Engine · RAG (Supabase) · Groq LLM")

# ---------- DATA FETCH ----------
@st.cache_data(ttl=30)
def get_history(limit=100):
    try:
        r = requests.get(f"{API_URL}/history", params={"limit": limit}, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Could not load history: {e}")
        return []

def run_investigation(transaction):
    r = requests.post(f"{API_URL}/investigate", json=transaction, timeout=90)
    r.raise_for_status()
    return r.json()

def run_chain_investigation(transactions):
    r = requests.post(f"{API_URL}/investigate-chain", json={"transactions": transactions}, timeout=180)
    r.raise_for_status()
    return r.json()

def make_case_id(item):
    raw = f"{item['created_at']}{item['transaction']['amount']}"
    return "CASE-" + hashlib.md5(raw.encode()).hexdigest()[:6].upper()

# ================= DASHBOARD =================
if page == "🏠 Dashboard":
    st.title("AI Fraud Investigation & Compliance Assistant")
    st.caption("Intelligent Transaction Monitoring and AML Risk Analysis")

    history = get_history(200)

    total = len(history)
    high = sum(1 for h in history if h["risk_tier"] == "High")
    medium = sum(1 for h in history if h["risk_tier"] == "Medium")
    low = sum(1 for h in history if h["risk_tier"] == "Low")
    avg_prob = (sum(h["fraud_probability"] for h in history) / total) if total else 0
    rule_hit_rate = (sum(1 for h in history if h.get("rule_flags")) / total * 100) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val, color in [
        (c1, "Total Investigations", total, "#e2e8f0"),
        (c2, "High Risk", high, "#ef4444"),
        (c3, "Medium Risk", medium, "#f59e0b"),
        (c4, "Avg Fraud Probability", f"{avg_prob:.3f}", "#e2e8f0"),
        (c5, "Rule Hit Rate", f"{rule_hit_rate:.1f}%", "#e2e8f0"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><p style="color:#64748b;font-size:12px;margin:0;text-transform:uppercase">{label}</p><h2 style="margin:6px 0;color:{color}">{val}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Fraud Probability Trend")
        if history:
            df = pd.DataFrame(history)
            df["created_at"] = pd.to_datetime(df["created_at"])
            df = df.sort_values("created_at")
            fig = px.line(df, x="created_at", y="fraud_probability", markers=True)
            fig.update_traces(line_color="#3b82f6")
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                               plot_bgcolor="#0d1526", paper_bgcolor="#0d1526",
                               font_color="#cbd5e1", xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No investigations yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Risk Distribution")
        if total:
            fig = go.Figure(data=[go.Pie(
                labels=["High", "Medium", "Low"], values=[high, medium, low], hole=0.55,
                marker_colors=["#ef4444", "#f59e0b", "#22c55e"]
            )])
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                               paper_bgcolor="#0d1526", font_color="#cbd5e1", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

# ================= INVESTIGATE =================
elif page == "🔎 Investigate":
    st.title("New Transaction Investigation")

    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        with st.form("investigation_form"):
            c1, c2 = st.columns(2)
            with c1:
                txn_type = st.selectbox("Transaction Type", ["CASH_OUT", "TRANSFER", "CASH_IN", "DEBIT", "PAYMENT"])
            with c2:
                step = st.number_input("Step", min_value=0, value=1)

            amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, format="%.2f")

            c3, c4 = st.columns(2)
            with c3:
                old_orig = st.number_input("Old Balance (Origin)", min_value=0.0, value=0.0, format="%.2f")
            with c4:
                new_orig = st.number_input("New Balance (Origin)", min_value=0.0, value=0.0, format="%.2f")

            c5, c6 = st.columns(2)
            with c5:
                old_dest = st.number_input("Old Balance (Destination)", min_value=0.0, value=0.0, format="%.2f")
            with c6:
                new_dest = st.number_input("New Balance (Destination)", min_value=0.0, value=0.0, format="%.2f")

            submitted = st.form_submit_button("🔍 Run Investigation", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        transaction = {
            "step": int(step), "type": txn_type, "amount": amount,
            "oldbalanceOrg": old_orig, "newbalanceOrig": new_orig,
            "oldbalanceDest": old_dest, "newbalanceDest": new_dest
        }
        with col2:
            status = st.empty()
            steps = [
                "🧠 Running XGBoost...",
                "📊 Computing SHAP values...",
                "🔎 Matching historical cases...",
                "🤖 Generating LLM report...",
            ]
            try:
                for msg in steps:
                    status.info(msg)
                    time.sleep(0.6)
                result = run_investigation(transaction)
                status.empty()
                st.session_state["last_result"] = result
                get_history.clear()
            except Exception as e:
                status.empty()
                st.error(f"Investigation failed: {e}")

    with col2:
        result = st.session_state.get("last_result")
        if result:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Investigation Result")

            risk = result["risk_tier"]
            prob = result["fraud_probability"]
            confidence = "High" if abs(prob - 0.5) > 0.35 or result.get("rule_flags") else "Medium"

            r1, r2, r3, r4 = st.columns(4)

            # --------------------------------------------------
            # Determine FINAL verdict from the LLM narrative
            # --------------------------------------------------
            final_risk = risk
            narrative = result.get("llm_narrative", "").lower()
            if "verdict: high" in narrative:
                final_risk = "High"
            elif "verdict: medium" in narrative:
                final_risk = "Medium"
            elif "verdict: low" in narrative:
                final_risk = "Low"
            final_color = RISK_COLORS.get(final_risk, "#64748b")

            # --------------------------------------------------
            # CARD 1 - FINAL RISK VERDICT
            # --------------------------------------------------
            with r1:
                st.markdown(
                    f"""
                    <div class="result-card">
                        <p class="label">Final Risk Verdict</p>
                        <p class="value"
                           style="color:{final_color};">
                           {final_risk}
                        </p>
                        <div class="risk-bar-bg">
                            <div class="risk-bar-fill"
                                 style="width:{prob*100:.0f}%;
                                        background:{final_color};">
                            </div>
                        </div>
                        <p style="
                            font-size:11px;
                            color:#94a3b8;
                            margin-top:8px;
                            margin-bottom:0;
                        ">
                            ML Model Score:
                            <b>{risk}</b>
                            ({prob*100:.1f}%)
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --------------------------------------------------
            # CARD 2 - PROBABILITY
            # --------------------------------------------------
            with r2:
                st.markdown(
                    f"""
                    <div class="result-card">
                        <p class="label">Fraud Probability</p>
                        <p class="value">{prob*100:.1f}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --------------------------------------------------
            # CARD 3 - RECOMMENDATION
            # --------------------------------------------------
            with r3:
                recommendation = (
                    "Escalate"
                    if final_risk == "High"
                    else "Review"
                    if final_risk == "Medium"
                    else "Approve"
                )
                rec_color = (
                    "#ef4444"
                    if final_risk == "High"
                    else "#f59e0b"
                    if final_risk == "Medium"
                    else "#22c55e"
                )
                st.markdown(
                    f"""
                    <div class="result-card">
                        <p class="label">Recommendation</p>
                        <p class="value"
                           style="color:{rec_color};
                                  font-size:17px;">
                           {recommendation}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --------------------------------------------------
            # CARD 4 - CONFIDENCE
            # --------------------------------------------------
            with r4:
                st.markdown(
                    f"""
                    <div class="result-card">
                        <p class="label">Confidence</p>
                        <p class="value"
                           style="font-size:17px;">
                           {confidence}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            if result.get("rule_flags"):
                st.markdown("**🚩 Rule-Based Red Flags**")
                for flag in result["rule_flags"]:
                    st.warning(flag)

            if result.get("top_features"):
                st.markdown("**📊 Top SHAP Features** (sorted by absolute impact)")
                shap_df = pd.DataFrame(result["top_features"])
                shap_df["abs_impact"] = shap_df["impact"].abs()
                shap_df = shap_df.sort_values("abs_impact", ascending=True)
                shap_df["direction"] = shap_df["impact"].apply(lambda x: "Pushes toward Fraud" if x > 0 else "Pushes toward Legitimate")
                fig = px.bar(
                    shap_df, x="impact", y="feature", orientation="h", color="direction",
                    color_discrete_map={"Pushes toward Fraud": "#ef4444", "Pushes toward Legitimate": "#3b82f6"}
                )
                fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10),
                                   plot_bgcolor="#0d1526", paper_bgcolor="#0d1526", font_color="#cbd5e1",
                                   legend=dict(orientation="h", yanchor="bottom", y=-0.4),
                                   xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
                st.plotly_chart(fig, use_container_width=True)

            if result.get("similar_cases"):
                st.markdown("**📁 Similar Historical Cases**")
                for c in result["similar_cases"]:
                    st.info(f"{c['section']} — {c['similarity']*100:.1f}% match")

            if result.get("llm_narrative"):
                st.markdown("**🧠 Compliance Analyst Report**")
                st.write(result["llm_narrative"])

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.info("Fill out the form and click Run Investigation to see results here.")
            st.markdown('</div>', unsafe_allow_html=True)


# ================= CHAIN INVESTIGATION =================
elif page == "🔗 Chain Investigation":
    st.title("Multi-Hop Transaction Chain Investigation")
    st.caption("Analyze a sequence of linked transactions (e.g. TRANSFER → CASH_OUT) to detect patterns invisible to single-transaction scoring.")

    col_form, col_result = st.columns([1, 1.3])

    with col_form:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"Transaction Chain ({len(st.session_state.chain_hops)} hops)")

        for i, hop in enumerate(st.session_state.chain_hops):
            with st.expander(f"Hop {i+1}: {hop['type']} — ₹{hop['amount']:,.2f}", expanded=(i == len(st.session_state.chain_hops) - 1)):
                c1, c2 = st.columns(2)
                with c1:
                    hop["type"] = st.selectbox(
                        "Transaction Type", ["CASH_OUT", "TRANSFER", "CASH_IN", "DEBIT", "PAYMENT"],
                        index=["CASH_OUT", "TRANSFER", "CASH_IN", "DEBIT", "PAYMENT"].index(hop["type"]),
                        key=f"type_{i}"
                    )
                with c2:
                    hop["step"] = st.number_input("Step", min_value=0, value=hop["step"], key=f"step_{i}")

                hop["amount"] = st.number_input("Amount (₹)", min_value=0.0, value=hop["amount"], format="%.2f", key=f"amount_{i}")

                c3, c4 = st.columns(2)
                with c3:
                    hop["oldbalanceOrg"] = st.number_input("Old Balance (Origin)", min_value=0.0, value=hop["oldbalanceOrg"], format="%.2f", key=f"oldorg_{i}")
                with c4:
                    hop["newbalanceOrig"] = st.number_input("New Balance (Origin)", min_value=0.0, value=hop["newbalanceOrig"], format="%.2f", key=f"neworg_{i}")

                c5, c6 = st.columns(2)
                with c5:
                    hop["oldbalanceDest"] = st.number_input("Old Balance (Destination)", min_value=0.0, value=hop["oldbalanceDest"], format="%.2f", key=f"olddest_{i}")
                with c6:
                    hop["newbalanceDest"] = st.number_input("New Balance (Destination)", min_value=0.0, value=hop["newbalanceDest"], format="%.2f", key=f"newdest_{i}")

                if len(st.session_state.chain_hops) > 1:
                    if st.button(f"🗑️ Remove Hop {i+1}", key=f"remove_{i}"):
                        st.session_state.chain_hops.pop(i)
                        st.rerun()

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("➕ Add Another Hop", use_container_width=True):
                last = st.session_state.chain_hops[-1]
                st.session_state.chain_hops.append({
                    "step": last["step"], "type": "CASH_OUT", "amount": 0.0,
                    "oldbalanceOrg": last["newbalanceDest"], "newbalanceOrig": 0.0,
                    "oldbalanceDest": 0.0, "newbalanceDest": 0.0
                })
                st.rerun()
        with bcol2:
            run_chain = st.button("🔗 Run Chain Investigation", type="primary", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if run_chain:
        with col_result:
            status = st.empty()
            steps_msgs = [
                "🧠 Running XGBoost on each hop...",
                "📊 Computing SHAP values...",
                "🔎 Matching historical cases...",
                "🔗 Analyzing cross-transaction patterns...",
                "🤖 Generating chain summary...",
            ]
            try:
                for msg in steps_msgs:
                    status.info(msg)
                    time.sleep(0.5)
                chain_result = run_chain_investigation(st.session_state.chain_hops)
                status.empty()
                st.session_state["last_chain_result"] = chain_result
                get_history.clear()
            except Exception as e:
                status.empty()
                st.error(f"Chain investigation failed: {e}")

    with col_result:
        chain_result = st.session_state.get("last_chain_result")
        if chain_result:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Chain Summary")

            overall = chain_result["overall_risk"]
            overall_color = RISK_COLORS.get(overall, "#64748b")

            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(f'''<div class="result-card">
                    <p class="label">Overall Risk</p>
                    <p class="value" style="color:{overall_color}">{overall}</p></div>''', unsafe_allow_html=True)
            with s2:
                st.markdown(f'''<div class="result-card">
                    <p class="label">Hop Count</p>
                    <p class="value">{chain_result["hop_count"]}</p></div>''', unsafe_allow_html=True)
            with s3:
                st.markdown(f'''<div class="result-card">
                    <p class="label">Avg Probability</p>
                    <p class="value">{chain_result["average_probability"]*100:.1f}%</p></div>''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if chain_result.get("chain_flags"):
                st.markdown("**🚩 Chain-Level Red Flags** (patterns only visible across hops)")
                for flag in chain_result["chain_flags"]:
                    st.error(flag)
            else:
                st.info("No cross-transaction patterns detected.")

            st.markdown("**📈 Risk Trend Across Hops**")
            hop_probs = [h["fraud_probability"] for h in chain_result["hops"]]
            hop_labels = [f"Hop {i+1}" for i in range(len(hop_probs))]
            trend_fig = px.line(x=hop_labels, y=hop_probs, markers=True)
            trend_fig.update_traces(line_color="#3b82f6")
            trend_fig.update_layout(
                height=220, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#0d1526", paper_bgcolor="#0d1526", font_color="#cbd5e1",
                xaxis=dict(gridcolor="#1e293b", title=""), yaxis=dict(gridcolor="#1e293b", title="Fraud Probability")
            )
            st.plotly_chart(trend_fig, use_container_width=True)

            st.markdown("**🔍 Individual Hop Details**")
            for i, hop in enumerate(chain_result["hops"]):
                hop_color = RISK_COLORS.get(hop["risk_tier"], "#64748b")
                with st.expander(f"Hop {i+1}: {hop['transaction']['type']} — ₹{hop['transaction']['amount']:,.2f} — {hop['risk_tier']} Risk"):
                    hc1, hc2 = st.columns(2)
                    with hc1:
                        st.write(f"**Model Probability:** {hop['fraud_probability']*100:.2f}%")
                        st.write(f"**Final Verdict:** {hop['risk_tier']}")
                    with hc2:
                        st.write(f"**Model-only tier:** {hop['model_risk_tier']}")

                    if hop.get("rule_flags"):
                        st.markdown("*Rule Flags:*")
                        for flag in hop["rule_flags"]:
                            st.warning(flag)

                    if hop.get("similar_cases"):
                        st.markdown("*Similar Cases:*")
                        for c in hop["similar_cases"]:
                            st.info(f"{c['section']} — {c['similarity']*100:.1f}% match")

                    if hop.get("llm_narrative"):
                        st.markdown("*Analyst Report:*")
                        st.write(hop["llm_narrative"])

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.info("Build a transaction chain on the left and click Run Chain Investigation.")
            st.markdown('</div>', unsafe_allow_html=True)

# ================= HISTORY =================
elif page == "📚 Investigation History":
    st.title("Investigation History")
    history = get_history(200)

    if history:
        table_data = []
        for h in history:
            risk = h["risk_tier"]
            table_data.append({
                "Case ID": make_case_id(h),
                "Time": h["created_at"][:19].replace("T", " "),
                "Investigator": "AI Analyst (Groq)",
                "Status": risk,
                "Recommendation": RISK_ACTION.get(risk, "Review"),
            })
        df = pd.DataFrame(table_data)

        risk_filter = st.multiselect("Filter by Status", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
        filtered_indices = [i for i, row in enumerate(table_data) if row["Status"] in risk_filter]
        filtered_df = df.iloc[filtered_indices].reset_index(drop=True)
        filtered_history = [history[i] for i in filtered_indices]

        def highlight_status(val):
            color = RISK_COLORS.get(val, "#64748b")
            return f'color: {color}; font-weight: 600'

        st.caption("Click a row to view full case details below.")
        event = st.dataframe(
            filtered_df.style.map(highlight_status, subset=["Status"]),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        selected_rows = event.selection.rows if event and event.selection else []

        if selected_rows:
            idx = selected_rows[0]
            item = filtered_history[idx]
            case_id = filtered_df.iloc[idx]["Case ID"]
            txn = item["transaction"]
            risk = item["risk_tier"]
            color = RISK_COLORS.get(risk, "#64748b")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"Case Details — {case_id}")

            colA, colB, colC = st.columns(3)
            with colA:
                st.markdown("**Transaction Details**")
                st.write(f"Type: `{txn['type']}`")
                st.write(f"Amount: ₹{txn['amount']:,.2f}")
                st.write(f"Step: {txn['step']}")
            with colB:
                st.markdown("**Origin Balance**")
                st.write(f"Old: ₹{txn['oldbalanceOrg']:,.2f}")
                st.write(f"New: ₹{txn['newbalanceOrig']:,.2f}")
            with colC:
                st.markdown("**Destination Balance**")
                st.write(f"Old: ₹{txn['oldbalanceDest']:,.2f}")
                st.write(f"New: ₹{txn['newbalanceDest']:,.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            colD, colE = st.columns(2)
            with colD:
                st.markdown(f'''<div class="result-card">
                    <p class="label">Model Probability</p>
                    <p class="value">{item["fraud_probability"]*100:.2f}%</p></div>''', unsafe_allow_html=True)
            with colE:
                st.markdown(f'''<div class="result-card">
                    <p class="label">Final Verdict</p>
                    <p class="value" style="color:{color}">{risk}</p></div>''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if item.get("rule_flags"):
                st.markdown("**🚩 Rule Flags**")
                for flag in item["rule_flags"]:
                    st.warning(flag)

            if item.get("top_features"):
                st.markdown("**📊 Top SHAP Features**")
                shap_df = pd.DataFrame(item["top_features"])
                shap_df["abs_impact"] = shap_df["impact"].abs()
                shap_df = shap_df.sort_values("abs_impact", ascending=True)
                shap_df["direction"] = shap_df["impact"].apply(lambda x: "Pushes toward Fraud" if x > 0 else "Pushes toward Legitimate")
                fig = px.bar(
                    shap_df, x="impact", y="feature", orientation="h", color="direction",
                    color_discrete_map={"Pushes toward Fraud": "#ef4444", "Pushes toward Legitimate": "#3b82f6"}
                )
                fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10),
                                   plot_bgcolor="#0d1526", paper_bgcolor="#0d1526", font_color="#cbd5e1",
                                   legend=dict(orientation="h", yanchor="bottom", y=-0.4),
                                   xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
                st.plotly_chart(fig, use_container_width=True)

            if item.get("similar_cases"):
                st.markdown("**📁 Similar Historical Cases**")
                for c in item["similar_cases"]:
                    st.info(f"{c['section']} — {c['similarity']*100:.1f}% match")

            if item.get("llm_narrative"):
                st.markdown("**🧠 LLM Report**")
                st.write(item["llm_narrative"])

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No history yet.")

# ================= SETTINGS =================
elif page == "⚙️ Settings":
    st.title("Settings")
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("System Information")
    st.write(f"**API Endpoint:** `{API_URL}`")
    st.write("**Model:** XGBoost Pipeline (PR-AUC 0.9698)")
    st.write("**Explainability:** SHAP TreeExplainer")
    st.write("**Retrieval:** Supabase pgvector + Hugging Face Inference API")
    st.write("**LLM:** Groq — llama-3.3-70b-versatile")
    st.markdown('</div>', unsafe_allow_html=True)
