import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Planner IQ Copilot",
    layout="wide"
)

st.title("📊 Planner IQ Copilot")

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

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
        col for col in required_cols
        if col not in df.columns
    ]

    if missing:

        st.error(
            f"Missing columns: {missing}"
        )

    else:

        # --------------------------------------------------
        # KPI CALCULATIONS
        # --------------------------------------------------

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

        # --------------------------------------------------
        # ABC CLASSIFICATION
        # --------------------------------------------------

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

        def get_abc(value):

            if value <= 80:
                return "A"

            elif value <= 95:
                return "B"

            else:
                return "C"

        abc_df["ABC_Class"] = (
            abc_df["Cum_%"]
            .apply(get_abc)
        )

        df = df.merge(
            abc_df[
                ["Material", "ABC_Class"]
            ],
            on="Material",
            how="left"
        )

        # --------------------------------------------------
        # INVENTORY STATUS
        # --------------------------------------------------

        df["Inventory_Status"] = np.where(
            df["Inventory_Coverage"] > 3,
            "Excess Inventory",
            "Healthy"
        )

        # --------------------------------------------------
        # PLANNER PRIORITY
        # --------------------------------------------------

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

        # --------------------------------------------------
        # OVERALL KPI
        # --------------------------------------------------

        avg_accuracy = round(
            df["Forecast_Accuracy"].mean(),
            2
        )

        avg_mape = round(
            df["MAPE_%"].mean(),
            2
        )

        wape = round(
            (
                df["Absolute_Error"].sum()
                /
                df["Actual"].sum()
            )
            * 100,
            2
        )

        bias = round(
            (
                df["Forecast_Error"].sum()
                /
                df["Actual"].sum()
            )
            * 100,
            2
        )

        # --------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Forecast Accuracy",
            f"{avg_accuracy}%"
        )

        c2.metric(
            "MAPE",
            f"{avg_mape}%"
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

        # --------------------------------------------------
        # DATA
        # --------------------------------------------------

        st.dataframe(
            df,
            use_container_width=True
        )

        # --------------------------------------------------
        # CHAT
        # --------------------------------------------------

        question = st.chat_input(
            "Ask Planner IQ..."
        )

        if question:

            st.chat_message("user").write(
                question
            )

            q = question.lower()

            answer = ""

            if (
                "summary" in q
                or
                "overview" in q
                or
                "performance" in q
            ):

                answer = f"""
Forecast Accuracy: {avg_accuracy}%

MAPE: {avg_mape}%

WAPE: {wape}%

Bias: {bias}%

Total Materials: {len(df)}

Total Sales: {df['Actual'].sum():,.0f}
"""

            elif (
                "attention" in q
                or
                "focus" in q
                or
                "review" in q
            ):

                review_df = df[
                    df["Planner_Priority"]
                    ==
                    "Review Required"
                ]

                answer = review_df.to_string(
                    index=False
                )

            elif "highest sales" in q:

                row = df.loc[
                    df["Actual"].idxmax()
                ]

                answer = (
                    f"{row['Material']} has the highest sales "
                    f"({row['Actual']:,.0f})"
                )

            elif "lowest sales" in q:

                row = df.loc[
                    df["Actual"].idxmin()
                ]

                answer = (
                    f"{row['Material']} has the lowest sales "
                    f"({row['Actual']:,.0f})"
                )

            elif "a class" in q:

                answer = (
                    df[
                        df["ABC_Class"] == "A"
                    ]
                    .to_string(index=False)
                )

            elif "b class" in q:

                answer = (
                    df[
                        df["ABC_Class"] == "B"
                    ]
                    .to_string(index=False)
                )

            elif "c class" in q:

                answer = (
                    df[
                        df["ABC_Class"] == "C"
                    ]
                    .to_string(index=False)
                )

            elif (
                "inventory risk" in q
                or
                "excess stock" in q
            ):

                risk = df[
                    df["Inventory_Coverage"] > 3
                ]

                answer = risk.to_string(
                    index=False
                )

            elif (
                "forecast error" in q
                or
                "forecast miss" in q
            ):

                answer = (
                    df.sort_values(
                        "Absolute_Error",
                        ascending=False
                    )
                    .head(10)
                    .to_string(index=False)
                )

            else:

                material = df[
                    df["Material"]
                    .astype(str)
                    .str.lower()
                    == q
                ]

                if len(material) > 0:

                    row = material.iloc[0]

                    answer = f"""
Material: {row['Material']}

Forecast: {row['Forecast']}

Actual: {row['Actual']}

Forecast Accuracy: {row['Forecast_Accuracy']}%

MAPE: {row['MAPE_%']}%

Bias: {row['Bias_%']}%

ABC Class: {row['ABC_Class']}

Inventory Coverage: {row['Inventory_Coverage']}

Planner Priority: {row['Planner_Priority']}
"""

                else:

                    answer = """
Try asking:

Summary

Overall Performance

Highest Sales

Lowest Sales

Which Materials Need Attention

Inventory Risk

Excess Stock

Forecast Error

A Class

B Class

C Class

Or type a Material Code directly.
"""

            st.chat_message(
                "assistant"
            ).write(answer)
