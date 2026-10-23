import streamlit as st
import pandas as pd
import numpy as np

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Planner IQ Copilot",
    layout="wide"
)

st.title("📊 Planner IQ Copilot")
st.write("Ask planning questions like ChatGPT")

# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "xls"]
)

# ==================================================
# PROCESS FILE
# ==================================================

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

        # ==========================================
        # KPI CALCULATIONS
        # ==========================================

        df["Forecast_Error"] = (
            df["Forecast"] - df["Actual"]
        )

        df["Absolute_Error"] = (
            abs(df["Forecast_Error"])
        )

        df["Forecast_Accuracy"] = (
            100 -
            (
                abs(
                    df["Forecast"] -
                    df["Actual"]
                )
                /
                df["Actual"].replace(0, 1)
                * 100
            )
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

        # ==========================================
        # ABC CLASSIFICATION
        # ==========================================

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

        # ==========================================
        # OVERALL KPI
        # ==========================================

        mape = (
            (
                df["Absolute_Error"]
                /
                df["Actual"].replace(0, 1)
            ).mean()
            * 100
        )

        wape = (
            df["Absolute_Error"].sum()
            /
            df["Actual"].sum()
            * 100
        )

        bias = (
            df["Forecast_Error"].sum()
            /
            df["Actual"].sum()
            * 100
        )

        # ==========================================
        # DASHBOARD
        # ==========================================

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Forecast Accuracy",
            f"{df['Forecast_Accuracy'].mean():.1f}%"
        )

        c2.metric(
            "MAPE",
            f"{mape:.1f}%"
        )

        c3.metric(
            "WAPE",
            f"{wape:.1f}%"
        )

        c4.metric(
            "Bias %",
            f"{bias:.1f}%"
        )

        c5.metric(
            "Materials",
            len(df)
        )

        # ==========================================
        # DATAFRAME
        # ==========================================

        st.dataframe(
            df,
            use_container_width=True
        )

        # ==========================================
        # CHAT BOX
        # ==========================================

        question = st.text_input(
            "💬 Ask Planner IQ"
        )

        if question:

            q = question.lower().strip()

            # ======================================
            # MATERIAL SEARCH
            # ======================================

            material_match = df[
                df["Material"]
                .astype(str)
                .str.lower()
                == q
            ]

            if not material_match.empty:

                row = material_match.iloc[0]

                st.success(
                    f"""
Material: {row['Material']}

Forecast: {row['Forecast']}

Actual: {row['Actual']}

Forecast Accuracy: {row['Forecast_Accuracy']}%

Forecast Error: {row['Forecast_Error']}

Bias: {row['Bias_%']}%

Inventory: {row['Inventory']}

Inventory Coverage: {row['Inventory_Coverage']}

ABC Class: {row['ABC_Class']}
"""
                )

            # ======================================
            # OVERALL PERFORMANCE
            # ======================================

            elif any(
                x in q for x in [
                    "summary",
                    "overview",
                    "performance",
                    "forecast performance",
                    "business summary"
                ]
            ):

                st.subheader(
                    "Business Summary"
                )

                st.write(
                    f"Total Materials : {len(df)}"
                )

                st.write(
                    f"Total Forecast : {df['Forecast'].sum():,.0f}"
                )

                st.write(
                    f"Total Actual Sales : {df['Actual'].sum():,.0f}"
                )

                st.write(
                    f"Average Forecast Accuracy : {df['Forecast_Accuracy'].mean():.2f}%"
                )

                st.write(
                    f"MAPE : {mape:.2f}%"
                )

                st.write(
                    f"WAPE : {wape:.2f}%"
                )

            # ======================================
            # SALES
            # ======================================

            elif "highest sales" in q:

                row = df.loc[
                    df["Actual"].idxmax()
                ]

                st.write(
                    f"✅ {row['Material']} has highest sales ({row['Actual']:,.0f})"
                )

            elif "lowest sales" in q:

                row = df.loc[
                    df["Actual"].idxmin()
                ]

                st.write(
                    f"✅ {row['Material']} has lowest sales ({row['Actual']:,.0f})"
                )

            elif "top sales" in q:

                st.dataframe(
                    df.nlargest(
                        10,
                        "Actual"
                    )[
                        [
                            "Material",
                            "Actual",
                            "Forecast_Accuracy"
                        ]
                    ]
                )

            # ======================================
            # FORECAST ACCURACY
            # ======================================

            elif "best forecast" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmax()
                ]

                st.write(
                    f"{row['Material']} has best forecast accuracy {row['Forecast_Accuracy']}%"
                )

            elif "lowest forecast" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmin()
                ]

                st.write(
                    f"{row['Material']} has lowest forecast accuracy {row['Forecast_Accuracy']}%"
                )

            elif "poor accuracy" in q:

                st.dataframe(
                    df[
                        df["Forecast_Accuracy"] < 70
                    ]
                )

            # ======================================
            # INVENTORY
            # ======================================

            elif "high inventory" in q:

                st.dataframe(
                    df.nlargest(
                        10,
                        "Inventory"
                    )[
                        ["Material", "Inventory"]
                    ]
                )

            elif "inventory coverage" in q:

                st.dataframe(
                    df[
                        [
                            "Material",
                            "Inventory",
                            "Inventory_Coverage"
                        ]
                    ]
                )

            elif "excess stock" in q:

                excess = df[
                    df["Inventory"]
                    >
                    (
                        df["Forecast"] * 2
                    )
                ]

                st.dataframe(excess)

            # ======================================
            # ABC CLASS
            # ======================================

            elif "a class" in q:

                st.dataframe(
                    df[
                        df["ABC_Class"] == "A"
                    ]
                )

            elif "b class" in q:

                st.dataframe(
                    df[
                        df["ABC_Class"] == "B"
                    ]
                )

            elif "c class" in q:

                st.dataframe(
                    df[
                        df["ABC_Class"] == "C"
                    ]
                )

            # ======================================
            # FORECAST BIAS
            # ======================================

            elif "over forecast" in q:

                st.dataframe(
                    df[
                        df["Forecast"]
                        >
                        df["Actual"]
                    ]
                )

            elif "under forecast" in q:

                st.dataframe(
                    df[
                        df["Forecast"]
                        <
                        df["Actual"]
                    ]
                )

            # ======================================
            # RISK MATERIALS
            # ======================================

            elif "risk" in q or "attention" in q:

                risk = df[
                    (
                        df["Forecast_Accuracy"] < 70
                    )
                    |
                    (
                        df["Inventory_Coverage"] > 3
                    )
                ]

                st.dataframe(risk)

            # ======================================
            # SOP SUMMARY
            # ======================================

            elif "sop" in q or "management" in q:

                poor = len(
                    df[
                        df["Forecast_Accuracy"]
                        < 70
                    ]
                )

                excessive = len(
                    df[
                        df["Inventory_Coverage"]
                        > 3
                    ]
                )

                st.markdown(
                    f"""
### Executive Summary

✅ Average Forecast Accuracy: **{df['Forecast_Accuracy'].mean():.1f}%**

✅ WAPE: **{wape:.1f}%**

⚠ Poor Accuracy Materials: **{poor}**

⚠ Excess Inventory Materials: **{excessive}**

📌 Focus on A-Class materials with low forecast accuracy.

📌 Review inventory coverage above 3 months.
"""
                )

            # ======================================
            # HELP
            # ======================================

            else:

                st.info(
                    """
Try asking:

• Summary

• Overall Forecast Performance

• Business Overview

• Highest Sales

• Lowest Sales

• Top Sales

• Best Forecast Accuracy

• Lowest Forecast Accuracy

• Poor Accuracy Materials

• High Inventory

• Inventory Coverage

• Excess Stock

• A Class Materials

• B Class Materials

• C Class Materials

• Over Forecast

• Under Forecast

• Risk Materials

• Materials Needing Attention

• Management Summary

• S&OP Summary

• Material Number (Example: 60270074)
"""
                )
