import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Planner IQ",
    layout="wide"
)

st.title("📊 Planner IQ - Demand Planning Copilot")

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

        # ==================================================
        # KPI CALCULATIONS
        # ==================================================

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

        # ==================================================
        # ABC CLASSIFICATION
        # ==================================================

        df = df.sort_values(
            by="Actual",
            ascending=False
        )

        df["Sales_%"] = (
            df["Actual"]
            /
            df["Actual"].sum()
            * 100
        )

        df["Cum_%"] = (
            df["Sales_%"].cumsum()
        )

        def abc(x):

            if x <= 80:
                return "A"

            elif x <= 95:
                return "B"

            else:
                return "C"

        df["ABC_Class"] = (
            df["Cum_%"].apply(abc)
        )

        # ==================================================
        # OVERALL KPI
        # ==================================================

        wape = (
            df["Absolute_Error"].sum()
            /
            df["Actual"].sum()
            * 100
        )

        mape = (
            (
                df["Absolute_Error"]
                /
                df["Actual"].replace(0, 1)
            ).mean()
            * 100
        )

        bias = (
            df["Forecast_Error"].sum()
            /
            df["Actual"].sum()
            * 100
        )

        # ==================================================
        # DASHBOARD
        # ==================================================

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
            "Bias",
            f"{bias:.1f}%"
        )

        c5.metric(
            "Materials",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        # ==================================================
        # CHATGPT STYLE QUESTION BOX
        # ==================================================

        question = st.text_input(
            "💬 Ask Planner IQ"
        )

        if question:

            q = question.lower().strip()

            # =======================================
            # MATERIAL SEARCH
            # =======================================

            material_df = df[
                df["Material"]
                .astype(str)
                .str.lower()
                == q
            ]

            if not material_df.empty:

                row = material_df.iloc[0]

                st.success(
                    f"""
Material : {row['Material']}

Forecast : {row['Forecast']}

Actual : {row['Actual']}

Forecast Accuracy : {row['Forecast_Accuracy']}%

Forecast Error : {row['Forecast_Error']}

Bias : {row['Bias_%']}%

Inventory : {row['Inventory']}

Inventory Coverage : {row['Inventory_Coverage']}

ABC Class : {row['ABC_Class']}
"""
                )

            # =======================================
            # SUMMARY
            # =======================================

            elif any(
                word in q
                for word in [
                    "summary",
                    "overview",
                    "dashboard",
                    "business summary"
                ]
            ):

                st.write("### Business Summary")

                st.write(
                    f"Total Materials : {len(df)}"
                )

                st.write(
                    f"Total Sales : {df['Actual'].sum():,.0f}"
                )

                st.write(
                    f"Total Forecast : {df['Forecast'].sum():,.0f}"
                )

                st.write(
                    f"Average Forecast Accuracy : {df['Forecast_Accuracy'].mean():.2f}%"
                )

                st.write(
                    f"WAPE : {wape:.2f}%"
                )

                st.write(
                    f"MAPE : {mape:.2f}%"
                )

            # =======================================
            # TOP SALES
            # =======================================

            elif "top" in q and "sales" in q:

                st.dataframe(
                    df.nlargest(
                        10,
                        "Actual"
                    )[[
                        "Material",
                        "Actual",
                        "Forecast_Accuracy"
                    ]]
                )

            # =======================================
            # HIGHEST SALES
            # =======================================

            elif "highest sales" in q:

                row = df.loc[
                    df["Actual"].idxmax()
                ]

                st.write(
                    f"{row['Material']} has highest sales ({row['Actual']})"
                )

            # =======================================
            # LOWEST SALES
            # =======================================

            elif "lowest sales" in q:

                row = df.loc[
                    df["Actual"].idxmin()
                ]

                st.write(
                    f"{row['Material']} has lowest sales ({row['Actual']})"
                )

            # =======================================
            # BEST FORECAST
            # =======================================

            elif "best forecast" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmax()
                ]

                st.write(
                    f"{row['Material']} has best forecast accuracy ({row['Forecast_Accuracy']}%)"
                )

            # =======================================
            # LOWEST FORECAST
            # =======================================

            elif "lowest forecast" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmin()
                ]

                st.write(
                    f"{row['Material']} has lowest forecast accuracy ({row['Forecast_Accuracy']}%)"
                )

            # =======================================
            # A CLASS
            # =======================================

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

            # =======================================
            # INVENTORY
            # =======================================

            elif "inventory coverage" in q:

                st.dataframe(
                    df[[
                        "Material",
                        "Inventory",
                        "Inventory_Coverage"
                    ]]
                )

            elif "high inventory" in q:

                st.dataframe(
                    df.nlargest(
                        10,
                        "Inventory"
                    )[[
                        "Material",
                        "Inventory"
                    ]]
                )

            # =======================================
            # EXCESS STOCK
            # =======================================

            elif "excess stock" in q:

                excess = df[
                    df["Inventory"]
                    >
                    (df["Forecast"] * 2)
                ]

                st.dataframe(excess)

            # =======================================
            # OVER FORECAST
            # =======================================

            elif "over forecast" in q:

                result = df[
                    df["Forecast"]
                    >
                    df["Actual"]
                ]

                st.dataframe(result)

            # =======================================
            # UNDER FORECAST
            # =======================================

            elif "under forecast" in q:

                result = df[
                    df["Forecast"]
                    <
                    df["Actual"]
                ]

                st.dataframe(result)

            # =======================================
            # RISK MATERIALS
            # =======================================

            elif (
                "risk" in q
                or
                "attention" in q
            ):

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

            # =======================================
            # MANAGEMENT SUMMARY
            # =======================================

            elif (
                "management"
                in q
                or
                "sop"
                in q
            ):

                poor = len(
                    df[
                        df["Forecast_Accuracy"] < 70
                    ]
                )

                excess = len(
                    df[
                        df["Inventory_Coverage"] > 3
                    ]
                )

                st.write(
                    f"""
### Management Summary

• Average Forecast Accuracy is {df['Forecast_Accuracy'].mean():.1f}%

• WAPE is {wape:.1f}%

• {poor} materials have poor forecast accuracy

• {excess} materials have excess inventory

• Focus on A-Class materials with low accuracy

• Review inventory coverage above 3 months
"""
                )

            # =======================================
            # DEFAULT RESPONSE
            # =======================================

            else:

                st.info(
                    """
Try asking:

• Summary

• Business Overview

• Top Sales

• Highest Sales

• Lowest Sales

• Best Forecast Accuracy

• Lowest Forecast Accuracy

• A Class Materials

• B Class Materials

• C Class Materials

• Excess Stock

• Inventory Coverage

• High Inventory

• Risk Materials

• Over Forecast

• Under Forecast

• Management Summary

• Material Code (Example: MAT1001)
"""
                )
