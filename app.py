import streamlit as st
import pandas as pd
import numpy as np

# =======================================================
# PAGE CONFIG
# =======================================================

st.set_page_config(
    page_title="Planner IQ ",
    layout="wide"
)

st.title("📊 Planner IQ ")
st.caption("AI Powered Demand Planning & Forecast Analytics")

# =======================================================
# FILE UPLOAD
# =======================================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "xls"]
)

# =======================================================
# PROCESS FILE
# =======================================================

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = [
        "Material",
        "Forecast",
        "Actual",
        "Inventory"
    ]

    missing = [
        col for col in required_cols
        if col not in df.columns
    ]

    if missing:

        st.error(
            f"Missing columns: {missing}"
        )

    else:

        # =======================================================
        # KPI CALCULATIONS
        # =======================================================

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

        # =======================================================
        # ABC CLASSIFICATION
        # =======================================================

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
            how="left",
            on="Material"
        )

        # =======================================================
        # INVENTORY STATUS
        # =======================================================

        df["Inventory_Status"] = np.where(
            df["Inventory_Coverage"] > 3,
            "Excess Inventory",
            "Healthy"
        )

        # =======================================================
        # PLANNER PRIORITY
        # =======================================================

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

        # =======================================================
        # OVERALL KPIs
        # =======================================================

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

        forecast_accuracy = round(
            df["Forecast_Accuracy"].mean(),
            2
        )

        # =======================================================
        # DASHBOARD
        # =======================================================

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
            "Bias %",
            f"{bias}%"
        )

        c5.metric(
            "Materials",
            len(df)
        )

        # =======================================================
        # DISPLAY DATA
        # =======================================================

        st.dataframe(
            df,
            use_container_width=True
        )

        # =======================================================
        # CHAT SECTION
        # =======================================================

        question = st.text_input(
            "💬 Ask Planner IQ"
        )

        if question:

            q = question.lower().strip()

            # ===================================================
            # MATERIAL SEARCH
            # ===================================================

            material_match = df[
                df["Material"]
                .astype(str)
                .str.lower()
                == q
            ]

            if not material_match.empty:

                row = material_match.iloc[0]

                st.success(f"""
Material : {row['Material']}

Forecast : {row['Forecast']:,.0f}

Actual : {row['Actual']:,.0f}

Forecast Accuracy : {row['Forecast_Accuracy']}%

MAPE : {row['MAPE_%']}%

Forecast Error : {row['Forecast_Error']:,.0f}

Bias : {row['Bias_%']}%

ABC Class : {row['ABC_Class']}

Inventory : {row['Inventory']:,.0f}

Inventory Coverage : {row['Inventory_Coverage']}

Forecast Status : {row['Forecast_Status']}

Priority : {row['Planner_Priority']}
""")

            # ===================================================
            # OVERVIEW
            # ===================================================

            elif any(x in q for x in [
                "summary",
                "overview",
                "performance",
                "forecast performance",
                "business summary"
            ]):

                st.markdown(f"""
### 📌 Executive Summary

✅ Forecast Accuracy = **{forecast_accuracy}%**

✅ MAPE = **{mape}%**

✅ WAPE = **{wape}%**

✅ Forecast Bias = **{bias}%**

✅ Total Forecast = **{df['Forecast'].sum():,.0f}**

✅ Total Sales = **{df['Actual'].sum():,.0f}**

✅ Total Materials = **{len(df)}**
""")

            # ===================================================
            # HIGHEST SALES
            # ===================================================

            elif "highest sales" in q:

                row = df.loc[
                    df["Actual"].idxmax()
                ]

                st.success(
                    f"{row['Material']} has highest sales ({row['Actual']:,.0f})"
                )

            # ===================================================
            # LOWEST SALES
            # ===================================================

            elif "lowest sales" in q:

                row = df.loc[
                    df["Actual"].idxmin()
                ]

                st.success(
                    f"{row['Material']} has lowest sales ({row['Actual']:,.0f})"
                )

            # ===================================================
            # BEST FORECAST ACCURACY
            # ===================================================

            elif "best forecast" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmax()
                ]

                st.success(
                    f"{row['Material']} has best forecast accuracy ({row['Forecast_Accuracy']}%)"
                )

 
