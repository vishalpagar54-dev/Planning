import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Planner IQ Copilot",
    layout="wide"
)

st.title("📊 Planner IQ Copilot")

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------

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
            f"Missing columns: {missing}"
        )

    else:

        # -------------------------------------------------
        # KPI CALCULATIONS
        # -------------------------------------------------

        df["Forecast_Error"] = (
            df["Forecast"] -
            df["Actual"]
        )

        df["Absolute_Error"] = abs(
            df["Forecast_Error"]
        )

        df["MAPE_%"] = (
            (
                abs(
                    df["Forecast"] -
                    df["Actual"]
                )
                /
                df["Actual"].replace(0, 1)
            ) * 100
        ).round(2)

        df["Forecast_Accuracy"] = (
            100 - df["MAPE_%"]
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

        df["Forecast_Status"] = np.where(
            df["Forecast"] > df["Actual"],
            "Over Forecast",
            "Under Forecast"
        )

        # -------------------------------------------------
        # ABC CLASSIFICATION
        # -------------------------------------------------

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

        def abc(x):

            if x <= 80:
                return "A"
            elif x <= 95:
                return "B"
            else:
                return "C"

        abc_df["ABC_Class"] = (
            abc_df["Cum_%"]
            .apply(abc)
        )

        df = df.merge(
            abc_df[
                ["Material", "ABC_Class"]
            ],
            on="Material",
            how="left"
        )

        # -------------------------------------------------
        # INVENTORY STATUS
        # -------------------------------------------------

        df["Inventory_Status"] = np.where(
            df["Inventory_Coverage"] > 3,
            "Excess Inventory",
            "Healthy"
        )

        # -------------------------------------------------
        # PRIORITY
        # -------------------------------------------------

        df["Planner_Priority"] = np.where(
            (
                df["Forecast_Accuracy"] < 70
            )
            |
            (
                df["Inventory_Coverage"] > 3
            ),
            "Review Required",
