import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Title
st.title("Tayara.tn Announcement Extractor")

# File uploader
uploaded_file = st.file_uploader("Upload Excel file containing raw announcements", type=["xlsx"])

# Helper function to parse each announcement block
def parse_announcement(text):
    # Initialize structured fields
    title = ""
    price = ""
    location = ""
    category = ""
    description = ""
    publisher = ""

    # Clean up
    text = re.sub(r"\s+", " ", text.strip())

    # Extract Title (bold or ### header like Markdown)
    title_match = re.search(r"(#+\s)?([A-ZÀ-ÿ0-9][^()]+?)\s?\(", text)
    if title_match:
        title = title_match.group(2).strip()
    else:
        # Fallback: First capitalized line
        first_line = re.match(r"^([A-ZÀ-ÿ][a-zA-Z0-9\s\-',]+)", text)
        if first_line:
            title = first_line.group(0).strip()

    # Extract Price (like 1200DT or 1 200 Dinars)
    price_match = re.search(r"([\d\s]+)(DT|Dinars|TND)", text)
    if price_match:
        price = price_match.group(1).replace(" ", "") + " " + price_match.group(2)

    # Extract Location (before words like 'minutes ago', 'hours ago', or a known city)
    loc_match = re.search(r"\b(Tunis|Ariana|Sfax|Sousse|Bizerte|Gabès|Gafsa|Kairouan|Mahdia|Monastir|Kébili|Kélibia|Ras[_\s]Jebel|Nabeul|Ben Arous|La Soukra)\b", text, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(0).title()

    # Extract Category (Maison, Terrain, Appartement, etc.)
    cat_match = re.search(r"(Maison|Terrain|Appartement|Autres Immobiliers|Bureaux|Commerce|Terrains et Fermes)", text, re.IGNORECASE)
    if cat_match:
        category = cat_match.group(0).title()

    # Extract Publisher name (before “publié par” or boutique name)
    pub_match = re.search(r"publié par ([A-Za-z0-9\s\-]+)", text, re.IGNORECASE)
    if pub_match:
        publisher = pub_match.group(1).strip()

    # Basic Description snippet
    desc_match = re.search(r"[Pp]ropose.*?\.", text)
    if desc_match:
        description = desc_match.group(0)

    return {
        "Title": title,
        "Price": price,
        "Location": location,
        "Category": category,
        "Publisher": publisher,
        "Description": description
    }

# Handle uploaded Excel file
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Detect column with raw text
        column_name = None
        for col in df.columns:
            if "text" in col.lower() or "data" in col.lower():
                column_name = col
                break
        if column_name is None:
            column_name = df.columns[0]

        # Process each row individually
        blocks = []
        for idx, row in df.iterrows():
            raw_text = str(row[column_name])
            if raw_text.strip():
                # Split by /item/ or other separators
                items = re.split(r"/item/|(?=\d{6,}/)", raw_text)
                blocks.extend(items)

        st.write(f"🧾 Detected {len(blocks)} announcements")

        # Process each block
        structured = [parse_announcement(b) for b in blocks if len(b.strip()) > 30]

        # Display result
        result_df = pd.DataFrame(structured)
        st.dataframe(result_df)

        # Download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Extracted Excel",
            data=output,
            file_name="tayara_announcements_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
