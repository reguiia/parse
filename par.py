import re
import pandas as pd

# List of major Tunisian cities and governorates (you can expand this)
TUNISIAN_LOCATIONS = [
    "Tunis", "Ariana", "Ben Arous", "La Marsa", "Manouba", "Nabeul", "Sousse", "Sfax",
    "Monastir", "Mahdia", "Gabès", "Médenine", "Tataouine", "Kairouan", "Kasserine", "Gafsa",
    "Kébili", "Tozeur", "Siliana", "Beja", "Bizerte", "Zaghouan", "Jendouba", "Le Kef"
]


def extract_location(text):
    for loc in TUNISIAN_LOCATIONS:
        if re.search(rf"\b{re.escape(loc)}\b", text, re.IGNORECASE):
            return loc
    return ""

def extract_announcements(raw_text):
    # Split each block by possible delimiter
    announcements = re.split(r'/item/|\n?\* \[', raw_text)
    structured = []

    for block in announcements:
        block = block.strip()
        if not block or "publié par" not in block:
            continue

        title_match = re.search(r'publié par .*? - (.*?) -', block)
        title = title_match.group(1).strip() if title_match else ""

        price_match = re.search(r'(\d+[.,]?\d*)\s?DT', block)
        price = price_match.group(0).strip() if price_match else ""

        location = extract_location(block)

        category_match = re.search(r'/Maisons|Villas|Terrains|Voitures|Immeubles|Appartements|Autres Immobiliers/', block)
        category = category_match.group(0).strip('/').strip() if category_match else ""

        contact_match = re.search(r'(\+216\s?\d{2,3}[\s\-\/]?\d{3}[\s\-\/]?\d{3})', block)
        contact = contact_match.group(1).strip() if contact_match else ""

        structured.append({
            "Title": title,
            "Price": price,
            "Location": location,
            "Category": category,
            "Contact": contact
        })

    return structured

# === I/O ===

input_path = "input_announcements.xlsx"
output_path = "structured_announcements.xlsx"

df = pd.read_excel(input_path)

all_announcements = []
for _, row in df.iterrows():
    raw_text = str(row.get("raw_data", ""))
    extracted = extract_announcements(raw_text)
    all_announcements.extend(extracted)

# Save
output_df = pd.DataFrame(all_announcements)
output_df.to_excel(output_path, index=False)

print(f"✅ Extracted {len(output_df)} announcements into '{output_path}'")
