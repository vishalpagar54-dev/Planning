import streamlit as st
import pandas as pd
import numpy as np

# Optional OpenAI
try:
    from openai import OpenAI
except:
    OpenAI = None

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Planner IQ Copilot",
    layout="wide"
)

st.title("📊 Planner IQ Copilot")
st.caption("AI Powered Demand Planning & Forecast Analytics")

# =====================================================
# OPENAI CLIENT
# =====================================================

client = None

try:
    if OpenAI:
        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )
except:
    client = None

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "xls"]
)

# =====================================================
# MAIN LOGIC
# =====================================================

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
            f"Missing columns: {missing}"
        )

        st.stop()

    # =====================================================
    # KPI CALCULATIONS
    # =====================================================

    df["Forecast_Error"] = (
        df["Forecast"] -
        df["Actual"]
    )

    df["Absolute_Error"] = (
        abs(df["Forecast_Error"])
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
        100 - df["MAPE_%"]
    ).clip(lower=0).round(2)

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

    df["Forecast_Status"] = np.where(
        df["Forecast"] > df["Actual"],
        "Over Forecast",
        "Under Forecast"
    )

    # =====================================================
    # ABC ANALYSIS
    # =====================================================

    abc_df = df.sort_values(
        by="Actual",
        ascending=False
    ).copy()

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
        else:
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

    # =====================================================
    # INVENTORY STATUS
    # =====================================================

    df["Inventory_Status"] = np.where(
        df["Inventory_Coverage"] > 3,
        "Excess Inventory",
        "Healthy"
    )

    # =====================================================
    # PLANNER PRIORITY
    # =====================================================

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

    # =====================================================
    # OVERALL KPIs
    # =====================================================

    forecast_accuracy = round(
        df["Forecast_Accuracy"].mean(),
        2
    )

    mape = round(
        df["MAPE_%"].mean(),
        2
    )

    wape = round(
        (
            df["Absolute_Error"].sum()
            /
            df["Actual"].sum()
        ) * 100,
        2
    )

    bias = round(
        (
            df["Forecast_Error"].sum()
            /
            df["Actual"].sum()
        ) * 100,
        2
    )

    # =====================================================
    # KPI DASHBOARD
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Forecast Accuracy",
        f"{forecast_accuracy}%"
    )

    c2.metric(
        "MAPE",
        f"{mape}%"
    )

    c3.metric(
        "WAPE",
        f"{wape}%"
    )

    c4.metric(
        "Bias",
        f"{bias}%"
    )

    c5.metric(
        "Materials",
        len(df)
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    # =====================================================
    # CHAT SECTION
    # =====================================================

    question = st.chat_input(
        "Ask Planner IQ..."
    )

    if question:

        with st.chat_message("user"):
            st.write(question)

        data_context = df.to_string(index=False)

        # =====================================================
        # GPT MODE
        # =====================================================

        if client:

            prompt = f"""
You are Planner IQ Copilot.

You are an expert in:

- Demand Planning
- Forecast Accuracy
- MAPE
- WAPE
- Forecast Bias
- Inventory Planning
- ABC Classification
- S&OP
- Demand Review

Planning Data:

{data_context}

Question:

{question}

Instructions:

1. Answer ONLY using uploaded data.
2. Provide business insights.
3. Provide recommendations.
4. Keep response professional.
5. Use bullet points when useful.
"""

            try:

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """
You are Planner IQ,
an expert Demand Planning,
Inventory and S&OP Copilot.
"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                with st.chat_message("assistant"):
                    st.write(answer)

            except Exception as e:

                st.error(
                    f"OpenAI Error: {str(e)}"
                )

        # =====================================================
        # FALLBACK MODE
        # =====================================================

        else:

            with st.chat_message("assistant"):

                st.warning(
                    "OpenAI API Key not configured."
                )

                st.markdown(f"""
### Quick Summary

✅ Forecast Accuracy: **{forecast_accuracy}%**

✅ MAPE: **{mape}%**

✅ WAPE: **{wape}%**

✅ Bias: **{bias}%**

✅ Total Materials: **{len(df)}**

### How to enable AI

Add this in Streamlit Secrets:

```toml
OPENAI_API_KEY="your-key"
