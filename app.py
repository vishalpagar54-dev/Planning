import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI

# ==========================================
# CONFIG
# ==========================================

st.set_page_config(
    page_title="Planner IQ Copilot",
    layout="wide"
)

st.title("📊 Planner IQ Copilot")

# ==========================================
# OPENAI KEY
# ==========================================

api_key = st.secrets.get("OPENAI_API_KEY", "")

# For local testing:
# api_key = "YOUR_API_KEY"

# ==========================================
# FILE UPLOAD
# ==========================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "xls"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = [
        "Material",
        "Forecast",
        "Actual",
        "Inventory"
    ]

    missing = [
        c for c in required_cols
        if c not in df.columns
    ]

    if missing:

        st.error(
            f"Missing Columns: {missing}"
        )

    else:

        # ======================================
        # KPI CALCULATIONS
        # ======================================

        df["Forecast_Error"] = (
            df["Forecast"] -
            df["Actual"]
        )

        df["Absolute_Error"] = abs(
            df["Forecast_Error"]
        )

        df["MAPE_%"] = (
            abs(
                df["Forecast"] -
                df["Actual"]
            )
            /
            df["Actual"].replace(0, 1)
            * 100
        ).round(2)

        df["Forecast_Accuracy"] = (
            100 -
            df["MAPE_%"]
        ).clip(lower=0)

        df["Bias_%"] = (
            df["Forecast_Error"]
            /
            df["Actual"].replace(0, 1)
            * 100
        ).round(2)

        df["Inventory_Coverage"] = (
            df["Inventory"]
            /
            df["Actual"].replace(0, 1)
        ).round(2)

        # ======================================
        # ABC CLASSIFICATION
        # ======================================

        abc_df = (
            df.sort_values(
                "Actual",
                ascending=False
            )
            .copy()
        )

        abc_df["Sales_%"] = (
            abc_df["Actual"]
            /
            abc_df["Actual"].sum()
            * 100
        )

        abc_df["Cum_%"] = (
            abc_df["Sales_%"]
            .cumsum()
        )

        def abc_class(x):

            if x <= 80:
                return "A"

            elif x <= 95:
                return "B"

            return "C"

        abc_df["ABC_Class"] = (
            abc_df["Cum_%"]
            .apply(abc_class)
        )

        df = df.merge(
            abc_df[
                ["Material", "ABC_Class"]
            ],
            on="Material",
            how="left"
        )

        # ======================================
        # STATUS FLAGS
        # ======================================

        df["Forecast_Status"] = np.where(
            df["Forecast"] > df["Actual"],
            "Over Forecast",
            "Under Forecast"
        )

        df["Inventory_Status"] = np.where(
            df["Inventory_Coverage"] > 3,
            "Excess Inventory",
            "Healthy"
        )

        df["Planner_Priority"] = np.where(
            (
                df["Forecast_Accuracy"] < 70
            )
            |
            (
                df["Inventory_Coverage"] > 3
            ),
            "Review Required",
            "Healthy"
        )

        # ======================================
        # OVERALL KPI
        # ======================================

        overall_accuracy = round(
            df["Forecast_Accuracy"].mean(),
            2
        )

        overall_mape = round(
            df["MAPE_%"].mean(),
            2
        )

        overall_wape = round(
            (
                df["Absolute_Error"].sum()
                /
                df["Actual"].sum()
            ) * 100,
            2
        )

        overall_bias = round(
            (
                df["Forecast_Error"].sum()
                /
                df["Actual"].sum()
            ) * 100,
            2
        )

        # ======================================
        # DASHBOARD
        # ======================================

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Forecast Accuracy",
            f"{overall_accuracy}%"
        )

        c2.metric(
            "MAPE",
            f"{overall_mape}%"
        )

        c3.metric(
            "WAPE",
            f"{overall_wape}%"
        )

        c4.metric(
            "Bias",
            f"{overall_bias}%"
        )

        c5.metric(
            "Materials",
            len(df)
        )

        # ======================================
        # DATA
        # ======================================

        st.dataframe(
            df,
            use_container_width=True
        )

        # ======================================
        # CHAT
        # ======================================

        question = st.chat_input(
            "Ask Planner IQ..."
        )

        if question:

            st.chat_message(
                "user"
            ).write(question)

            if not api_key:

                st.error(
                    "OpenAI API Key not configured."
                )

            else:

                client = OpenAI(
                    api_key=api_key
                )

                dataset_summary = f"""
Forecast Accuracy: {overall_accuracy}%

MAPE: {overall_mape}%

WAPE: {overall_wape}%

Bias: {overall_bias}%

Materials: {len(df)}
"""

                data_context = (
                    df.head(200)
                    .to_string(index=False)
                )

                prompt = f"""
You are Planner IQ.

You are a Demand Planning,
Forecasting,
Inventory,
S&OP,
and Supply Chain Copilot.

Business KPI:

{dataset_summary}

Dataset:

{data_context}

Question:

{question}

Answer using supply chain terminology.

Provide recommendations where possible.
"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt
                        }
                    ],
                    temperature=0.2
                )

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                st.chat_message(
                    "assistant"
                ).write(answer)
