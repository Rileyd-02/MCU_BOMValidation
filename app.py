import streamlit as st
import pandas as pd

st.set_page_config(page_title="PLM Monthly Comparison", layout="wide")

st.title("📊 PLM Monthly Excel Comparison Tool")
st.subheader("About tool")
st.write("Tool to map and compare PLM download similarities and detect supplier & attribute changes month to month")

prev_file = st.file_uploader("Upload Previous Month Excel", type=["xlsx"])
curr_file = st.file_uploader("Upload Current Month Excel", type=["xlsx"])

COMPARE_COLS = ["Style", "BOM", "Cycle", "Article", "Supplier"]

KEY_COLS = [
    "Season",
    "Style",
    "Article",
    "Type of Const 1",
    "UOM",
    "Composition",
    "Measurement",
    "Supplier Country"
]

if prev_file and curr_file:
    prev_df = pd.read_excel(prev_file).fillna("").astype(str)
    curr_df = pd.read_excel(curr_file).fillna("").astype(str)

    # Create row keys
    prev_df["ROW_KEY"] = prev_df[KEY_COLS].agg("|".join, axis=1)
    curr_df["ROW_KEY"] = curr_df[KEY_COLS].agg("|".join, axis=1)

    merged = curr_df.merge(
        prev_df,
        on="ROW_KEY",
        how="left",
        suffixes=("_CURR", "_PREV"),
        indicator=True
    )

    results = []

    for _, row in merged.iterrows():
        record = {"ROW_KEY": row["ROW_KEY"]}

        # New row check
        if row["_merge"] == "left_only":
            for col in COMPARE_COLS:
                record[f"{col}_Match"] = "New"
            record["Overall Status"] = "New Row"
            results.append(record)
            continue

        row_match = True

        for col in COMPARE_COLS:
            curr_val = row[f"{col}_CURR"]
            prev_val = row[f"{col}_PREV"]

            match = curr_val == prev_val
            record[f"{col}_Match"] = "Match" if match else "Mismatch"

            if not match:
                row_match = False

        record["Overall Status"] = "Match" if row_match else "Mismatch"
        results.append(record)

    result_df = pd.DataFrame(results)

    # ===== SUMMARY =====
    st.subheader("📌 Summary")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", len(result_df))
    col2.metric("Matched Rows", (result_df["Overall Status"] == "Match").sum())
    col3.metric("Changed Rows", (result_df["Overall Status"] == "Mismatch").sum())
    col4.metric("New Rows", (result_df["Overall Status"] == "New Row").sum())

    st.subheader("📉 Column-wise Mismatch Count")
    mismatch_summary = {
        col: (result_df[f"{col}_Match"] == "Mismatch").sum()
        for col in COMPARE_COLS
    }

    st.dataframe(
        pd.DataFrame.from_dict(mismatch_summary, orient="index", columns=["Mismatch Count"]),
        use_container_width=True
    )

    st.subheader("🔍 Detailed Comparison Preview")
    st.dataframe(result_df, use_container_width=True)

    st.download_button(
        "⬇️ Download Comparison Output",
        result_df.to_csv(index=False),
        "PLM_Monthly_Comparison.csv",
        "text/csv"
    )
