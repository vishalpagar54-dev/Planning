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
