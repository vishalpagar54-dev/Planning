import streamlit as st
import pandas as pd

st.set_page_config(page_title="Planning Copilot", layout="wide")

st.title("📊 Planning Copilot")

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

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")

    else:

        df["Forecast_Accuracy"] = (
            100
            - abs(df["Forecast"] - df["Actual"])
            / df["Actual"]
            * 100
        ).round(2)

        st.dataframe(df)

        question = st.text_input(
            "Ask a Question"
        )

        if question:

            q = question.lower()

            if "summary" in q:

                st.write(
                    f"Total Materials: {len(df)}"
                )

                st.write(
                    f"Total Sales: {df['Actual'].sum()}"
                )

                st.write(
                    f"Average Forecast Accuracy: {round(df['Forecast_Accuracy'].mean(),2)}%"
                )

            elif "lowest forecast accuracy" in q:

                row = df.loc[
                    df["Forecast_Accuracy"].idxmin()
                ]

                st.write(
                    f"{row['Material']} has lowest forecast accuracy"
                )

            elif "highest sales" in q:

                row = df.loc[
                    df["Actual"].idxmax()
                ]

                st.write(
                    f"{row['Material']} has highest sales"
                )

            else:

                st.write(
                    "Try: summary, lowest forecast accuracy, highest sales"
                )
