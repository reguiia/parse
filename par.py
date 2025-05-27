import streamlit as st
import pandas as pd
import re
from io import BytesIO

def parse_markdown(text):
    items = text.split("/item/")
    result = []

    for entry in items:
        if len(entry.strip()) < 20:
            continue

        # Placeholder logic — replace with real parsing
        title = re.search(r'## (.+)', entry)
        location = re.search(r'(\b[A-Z][a-z]+,\s?\d+ minutes ago\b)', entry)
        price = re.search(r'(\d{3,})DT', entry)

        result.append({
            "Title": title.group(1) if title else "",
            "Location": location.group(1) if location else "",
            "Price": price.group(1) if price else "",
            "Raw": entry.strip()
        })
    return result

st.title("Markdown Excel Parser")

uploaded_file = st.file_uploader("Upload Excel file with raw markdown", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "data" not in df.columns:
        st.error("Excel must contain a 'data' column with markdown content.")
    else:
        output_rows = []
        for _, row in df.iterrows():
            entries = parse_markdown(row["data"])
            output_rows.extend(entries)

        output_df = pd.DataFrame(output_rows)

        # Display preview
        st.dataframe(output_df.head())

        # Download button
        buffer = BytesIO()
        output_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="Download Result as Excel",
            data=buffer,
            file_name="parsed_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
