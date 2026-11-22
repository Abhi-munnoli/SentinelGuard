
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(
    page_title="SentinelGuard",
    page_icon="🛡️",
    layout="wide"
)

API = st.sidebar.text_input(
    "Backend API URL",
    "http://127.0.0.1:8000"
)

st.sidebar.title("🛡️ SentinelGuard")

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Analyze Transaction", "Transaction History"]
)


# -----------------------------
# API GET Function
# -----------------------------

def api_get(path):
    try:
        response = requests.get(
            API + path,
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(f"Cannot connect to API: {exc}")
        return None


# -----------------------------
# Explanation Display
# -----------------------------

def display_explanation(explanation):

    st.subheader("Explanation Signals")

    if not explanation:
        st.info("No explanation available.")
        return

    if isinstance(explanation, dict):
        explanation = [
            {"feature": key, "explanation": value}
            for key, value in explanation.items()
        ]

    if not isinstance(explanation, list):
        st.write(str(explanation))
        return

    clean_rows = []

    for item in explanation:

        if isinstance(item, dict):

            clean_rows.append({
                "Feature": str(
                    item.get("feature", "Unknown")
                ),
                "Value": str(
                    item.get("value", "N/A")
                ),
                "Explanation": str(
                    item.get(
                        "explanation",
                        item.get(
                            "description",
                            item.get("reason", "No details available")
                        )
                    )
                )
            })

        else:
            clean_rows.append({
                "Feature": "General",
                "Value": "-",
                "Explanation": str(item)
            })

    explanation_df = pd.DataFrame(clean_rows)

    st.dataframe(
        explanation_df,
        use_container_width=True,
        hide_index=True
    )


# -----------------------------
# Main Dashboard
# -----------------------------

st.title("🛡️ SentinelGuard")

st.caption(
    "Real-Time Banking Fraud Intelligence & Explainable Risk Scoring"
)


# =====================================================
# OVERVIEW PAGE
# =====================================================

if page == "Overview":

    metrics = api_get("/metrics")
    rows = api_get("/transactions?limit=500")

    if metrics:

        cols = st.columns(4)

        cols[0].metric(
            "Total transactions",
            metrics["total_transactions"]
        )

        cols[1].metric(
            "Predicted fraud",
            metrics["predicted_fraud"]
        )

        cols[2].metric(
            "Legitimate",
            metrics["legitimate"]
        )

        cols[3].metric(
            "High-risk alerts",
            metrics["high_risk"]
        )

    if rows is not None:

        df = pd.DataFrame(rows)

        if not df.empty:

            left, right = st.columns(2)

            with left:

                st.subheader("Risk Distribution")

                st.plotly_chart(
                    px.pie(
                        df,
                        names="risk_level",
                        hole=0.55
                    ),
                    use_container_width=True
                )

            with right:

                st.subheader("Risk Score Distribution")

                st.plotly_chart(
                    px.histogram(
                        df,
                        x="risk_score",
                        color="risk_level",
                        nbins=20
                    ),
                    use_container_width=True
                )

            st.subheader("Latest Transactions")

            st.dataframe(
                df[
                    [
                        "id",
                        "created_at",
                        "amount",
                        "risk_score",
                        "risk_level",
                        "prediction"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info(
                "No transactions yet. Analyze a transaction to populate the dashboard."
            )


# =====================================================
# ANALYZE TRANSACTION PAGE
# =====================================================

elif page == "Analyze Transaction":

    st.subheader("Analyze a Transaction")

    with st.form("transaction"):

        c1, c2, c3 = st.columns(3)

        amount = c1.number_input(
            "Amount (₹)",
            min_value=0.0,
            value=12500.0
        )

        hour = c2.slider(
            "Transaction Hour",
            0,
            23,
            2
        )

        distance = c3.number_input(
            "Distance from home (km)",
            min_value=0.0,
            value=450.0
        )

        merchant = c1.slider(
            "Merchant Risk",
            0.0,
            1.0,
            0.8
        )

        velocity = c2.number_input(
            "Recent Transaction Count",
            min_value=0,
            value=6
        )

        foreign = c3.selectbox(
            "Foreign Transaction",
            [0, 1],
            format_func=lambda x: "Yes" if x else "No"
        )

        device = c1.selectbox(
            "New Device",
            [0, 1],
            format_func=lambda x: "Yes" if x else "No"
        )

        submitted = st.form_submit_button(
            "Analyze Transaction",
            type="primary"
        )

    if submitted:

        payload = {
            "amount": amount,
            "hour": hour,
            "distance_from_home": distance,
            "merchant_risk": merchant,
            "transaction_velocity": velocity,
            "is_foreign": foreign,
            "device_changed": device
        }

        try:

            response = requests.post(
                API + "/predict",
                json=payload,
                timeout=30
            )

            if response.ok:

                result = response.json()

                st.success(
                    f"Analysis completed — Transaction #{result['transaction_id']}"
                )

                a, b, c = st.columns(3)

                a.metric(
                    "Fraud Probability",
                    f"{result['fraud_probability'] * 100:.1f}%"
                )

                b.metric(
                    "Risk Score",
                    f"{result['risk_score']}/100"
                )

                c.metric(
                    "Risk Level",
                    result["risk_level"]
                )

                st.progress(
                    max(0, min(100, int(result["risk_score"])))
                )

                # Display readable explanations
                display_explanation(
                    result.get("explanation", [])
                )

                st.warning(
                    "Risk score is decision support, not proof of fraud. Use human review."
                )

            else:

                st.error(
                    f"API Error: {response.text}"
                )

        except requests.RequestException as exc:

            st.error(
                f"Request failed: {exc}"
            )


# =====================================================
# TRANSACTION HISTORY PAGE
# =====================================================

else:

    st.subheader("Transaction History")

    rows = api_get("/transactions?limit=1000")

    if rows is not None:

        df = pd.DataFrame(rows)

        if not df.empty:

            levels = st.multiselect(
                "Filter by Risk Level",
                ["Low", "Medium", "High"],
                default=["Low", "Medium", "High"]
            )

            view = df[
                df["risk_level"].isin(levels)
            ]

            st.dataframe(
                view.drop(columns=["explanation"], errors="ignore"),
                use_container_width=True,
                hide_index=True
            )

            # Expandable explanations for each transaction
            st.subheader("Transaction Explanations")

            for _, row in view.iterrows():

                with st.expander(
                    f"Transaction #{row['id']} — {row['risk_level']} Risk"
                ):

                    st.write(
                        f"**Amount:** ₹{row['amount']}"
                    )

                    st.write(
                        f"**Risk Score:** {row['risk_score']}/100"
                    )

                    display_explanation(
                        row.get("explanation", [])
                    )

            st.download_button(
                "Download CSV Report",
                view.drop(
                    columns=["explanation"],
                    errors="ignore"
                ).to_csv(index=False),
                file_name="sentinelguard_transactions.csv",
                mime="text/csv"
            )

        else:

            st.info(
                "No transactions stored yet."
            )
