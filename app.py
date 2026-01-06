import streamlit as st
import pandas as pd

st.set_page_config(page_title="PLM Monthly Comparison", layout="wide")

st.title("📊 PLM Monthly Excel Comparison Tool")

prev_file = st.file_uploader("Upload Previous Month Excel", type=["xlsx"])
curr_file = st.file_uploader("Upload Current Month Excel", type=["xlsx"])

# Columns to compare
COMPARE_COLS = ["Style", "BOM", "Cycle", "Article", "Supplier"]

if prev_file and curr_file:
    # Load data
    prev_df = pd.read_excel(prev_file)
    curr_df = pd.read_excel(curr_file)

    # Ensure same column order
    prev_df = prev_df.fillna("").astype(str)
    curr_df = curr_df.fillna("").astype(str)

    # Create unique row key using A:L
    prev_df["ROW_KEY"] = prev_df.iloc[:, 0:12].agg("|".join, axis=1)
    curr_df["ROW_KEY"] = curr_df.iloc[:, 0:12].agg("|".join, axis=1)

    # Merge datasets
    merged = curr_df.merge(
        prev_df,
        on="ROW_KEY",
        how="left",
        suffixes=("_CURR", "_PREV")
    )

    results = []

    for _, row in merged.iterrows():
        record = {
            "ROW_KEY": row["ROW_KEY"]
        }

        row_match = True

        for col in COMPARE_COLS:
            curr_val = row[f"{col}_CURR"]
            prev_val = row.get(f"{col}_PREV", "")

            match = curr_val == prev_val
            record[f"{col}_Match"] = "Match" if match else "Mismatch"

            if not match:
                row_match = False

        record["Overall Status"] = "Match" if row_match else "Mismatch"
        results.append(record)

    result_df = pd.DataFrame(results)

    # Summary
    total_rows = len(result_df)
    matched_rows = (result_df["Overall Status"] == "Match").sum()
    mismatched_rows = total_rows - matched_rows

    st.subheader("📌 Summary")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Rows Compared", total_rows)
    col2.metric("Fully Matched Rows", matched_rows)
    col3.metric("Rows with Changes", mismatched_rows)

    # Column-wise mismatch summary
    st.subheader("📉 Column-wise Mismatch Count")
    mismatch_summary = {
        col: (result_df[f"{col}_Match"] == "Mismatch").sum()
        for col in COMPARE_COLS
    }

    st.dataframe(
        pd.DataFrame.from_dict(mismatch_summary, orient="index", columns=["Mismatch Count"])
    )

    # Preview
    st.subheader("🔍 Detailed Comparison Preview")
    st.dataframe(result_df, use_container_width=True)

    # Download result
    st.download_button(
        label="⬇️ Download Comparison Output",
        data=result_df.to_csv(index=False),
        file_name="PLM_Monthly_Comparison.csv",
        mime="text/csv"
    )
