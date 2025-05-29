# Step 1: Install required packages
#!pip install requests beautifulsoup4 pandas openpyxl --quiet

# Step 2: Import libraries
import requests
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import smtplib
from datetime import datetime
import re
 #from google.colab import drive
 #from google.colab import files
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

soup = BeautifulSoup(html_content, 'lxml')

# --- Functions for Tayara.tn ---
def fetch_tayara(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Fetched tayara.tn page {url}")
        return response.text
    else:
        print(f"❌ Failed ({response.status_code}) on tayara.tn: {url}")
        return None

def extract_tayara_articles(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all("article", class_="mx-0")

def parse_tayara_article(article):
    try:
        base_url = "https://www.tayara.tn "
        a_tag = article.find('a', href=True)
        ad_url = base_url + a_tag['href'] if a_tag else None

        card = article.find('div', class_='flex-col')
        if not card:
            return {}

        # Title
        title_tag = card.find('h2')
        title = title_tag.get_text(strip=True) if title_tag else None

        # Price
        price_data = card.find('data', class_='font-bold')
        full_price = price_data.get_text(strip=True) if price_data else ''
        price = ''.join(filter(str.isdigit, full_price.split('DT')[0])) if 'DT' in full_price else ''

        # Category & Property Type
        category_span = card.find('span', class_='text-neutral-500')
        category = category_span.get_text(strip=True) if category_span else None
        prop_type = category.split(',')[0].strip() if category else None

        # Location & Posted Time
        location_divs = card.find_all('div', class_='text-gray-800')
        location = posted = None
        for div in location_divs:
            svg = div.find('svg')
            if svg:
                txt = div.get_text(strip=True)
                if ',' in txt:
                    parts = txt.split(',', 1)
                    location = parts[0].strip()
                    posted = parts[1].strip()

        # Image info
        img_tag = card.find('img')
        img_alt = img_tag.get('alt', '') if img_tag else ''
        image_url = img_tag.get('src', '') if img_tag else ''

        # Extract number of rooms (e.g., S+1, S+2)
        room_match = re.search(r"S\+\d+", (title or '') + ' ' + (img_alt or ''), re.IGNORECASE)
        rooms = room_match.group(0) if room_match else None

        # Extract amenities
        amenities = []
        keywords = ['wifi', 'climatiseur', 'chauffage', 'terrasse', 'meublé', 'garage']
        for word in keywords:
            if word.lower() in ((title or '') + ' ' + (img_alt or '')).lower():
                amenities.append(word.capitalize())

        return {
            'Title': title,
            'Price (DT)': price,
            'Type': prop_type,
            'Category': category,
            'Location': location,
            'Posted': posted,
            'Link': ad_url,
            'Rooms': rooms,
            'Amenities': ', '.join(amenities),
            'Image Alt Text': img_alt,
            'Image URL': image_url
        }

    except Exception as e:
        print(f"⚠️ Error parsing tayara listing: {e}")
        return {}

# --- Functions for Tunisie-Annonce.com ---
def fetch_tunisie_annonce(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Fetched tunisie-annonce.com page {url}")
        return response.text
    else:
        print(f"❌ Failed ({response.status_code}) on tunisie-annonce.com: {url}")
        return None

def extract_tunisie_annonce_rows(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all('tr', class_='Tableau1')

def parse_tunisie_annonce_row(row):
    cells = row.find_all('td')
    if len(cells) < 10:
        return {}

    # Gouvernorat, Délégation, Localité
    location_cell = cells[1].find('a', onmouseover=True)
    gov = del_ = loc = None
    if location_cell:
        hover_text = location_cell['onmouseover']
        gov_match = re.search(r"<b>Gouvernorat</b> : (.+?)<br/>", hover_text)
        del_match = re.search(r"<b>Délégation</b> : (.+?)<br/>", hover_text)
        loc_match = re.search(r"<b>Localité</b> : (.+?)\"", hover_text)
        gov = gov_match.group(1) if gov_match else None
        del_ = del_match.group(1) if del_match else None
        loc = loc_match.group(1) if loc_match else None
    region = f"{gov}, {del_}" if gov or del_ else loc

    # Nature & Type
    nature_type_cell = cells[3]
    nature_tooltip = nature_type_cell.get('onmouseover', '')
    nat_match = re.search(r"<b>Nature</b> : (.+?)<br/>", nature_tooltip)
    typ_match = re.search(r"<b>Type</b> : (.+?)\"", nature_tooltip)
    nature = nat_match.group(1) if nat_match else None
    prop_type = typ_match.group(1) if typ_match else None

    # Title / Description
    desc_link = cells[7].find('a', onmouseover=True)
    title = description = link = None
    if desc_link:
        hover_text = desc_link['onmouseover']
        title_match = re.search(r"<b>(.+?)</b><br/>", hover_text)
        desc_match = re.search(r"<br/>(.+?)<br/>", hover_text)
        title = title_match.group(1) if title_match else None
        description = desc_match.group(1) if desc_match else None
        link = "http://www.tunisie-annonce.com/" + desc_link.get('href', '') if desc_link.get('href') else None

    # Price
    price_cell = cells[9]
    price = price_cell.get_text(strip=True)
    price = ''.join(filter(str.isdigit, price)) if price else None

    # Posted date
    posted_cell = cells[11]
    posted = posted_cell.get_text(strip=True) if posted_cell else None

    # Image Info
    image_tag = cells[7].find('img', src=True)
    image_alt = image_tag.get('alt', '') if image_tag else ''
    image_url = "http://www.tunisie-annonce.com/" + image_tag['src'] if image_tag else None

    # Extract number of rooms
    room_match = re.search(r"S\+\d+", (title or '') + ' ' + (description or '') + ' ' + (image_alt or ''), re.IGNORECASE)
    rooms = room_match.group(0) if room_match else None

    # Extract amenities
    amenities = []
    keywords = ['wifi', 'climatiseur', 'chauffage', 'terrasse', 'meublé', 'garage']
    for word in keywords:
        if word.lower() in ((title or '') + ' ' + (description or '') + ' ' + (image_alt or '')).lower():
            amenities.append(word.capitalize())

    return {
        'Title': title,
        'Price (DT)': price,
        'Type': prop_type,
        'Category': nature,
        'Location': region,
        'Posted': posted,
        'Link': link,
        'Rooms': rooms,
        'Amenities': ', '.join(amenities),
        'Image Alt Text': image_alt,
        'Image URL': image_url
    }

# --- Main Scraping Logic ---
all_ads = []

# Scrape Tayara.tn (pages 1–5)
for i in range(1, 6):
    url = f"https://www.tayara.tn/ads/c/Immobilier/?page= {i}"
    html = fetch_tayara(url)
    if html:
        articles = extract_tayara_articles(html)
        for article in articles:
            parsed = parse_tayara_article(article)
            if parsed:
                all_ads.append(parsed)
    sleep(1)

# Scrape Tunisie-Annonce.com (pages 1–5)
base_url = "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_cat=1&page="
for i in range(1, 6):
    url = base_url + str(i)
    html = fetch_tunisie_annonce(url)
    if html:
        rows = extract_tunisie_annonce_rows(html)
        for row in rows:
            parsed = parse_tunisie_annonce_row(row)
            if parsed:
                all_ads.append(parsed)
    sleep(1)

# --- Export to CSV and XLSX ---
df = pd.DataFrame(all_ads)

print(f"\n📦 Total ads parsed: {len(df)}")

# Show full DataFrame
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    display(df)

# Save to CSV
df.to_csv("real_estate_combined.csv", index=False)
print("\n📄 CSV file created: real_estate_combined.csv")

# Save to Excel
try:
    df.to_excel("real_estate_combined.xlsx", index=False, engine='openpyxl')
    print("📊 Excel file created: real_estate_combined.xlsx")
    files.download("real_estate_combined.xlsx")
except Exception as e:
    print(f"❌ Error saving Excel: {e}")

  # Generate shareable link manually from Drive UI or use API
file_link = "https://colab.research.google.com/drive/1EEG72YYgqefphnOAYjlPRhng7Tt6fTsF?usp=sharing"  # Replace with actual link

# --- Send via Email ---
def send_email(sender_email, sender_password, receiver_email, file_path):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f'Real Estate Listings - {datetime.now().strftime("%Y-%m-%d")}'
    part = MIMEBase('application', "octet-stream")
    with open(file_path, "rb") as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{file_path.split("/")[-1]}"')
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print("📧 Email sent successfully.")

# --- Send via WhatsApp ---
#def send_whatsapp_message(account_sid, auth_token, from_number, to_number, file_link):
 #   client = Client(account_sid, auth_token)
  #  message = client.messages.create(
  #      body=f"📊 Real Estate Listings:\n{file_link}",
  #      from_=f'whatsapp:{from_number}',
  #      to=f'whatsapp:{to_number}'
   # )
 #   print(f"💬 WhatsApp message sent (SID: {message.sid})")

# --- Set Up Credentials and Trigger Sending ---
try:
    # Gmail credentials
    gmail_user = "alatestreg@gmail.com"
    gmail_app_password = "eqcx prwx ccbx ciur"

    # WhatsApp credentials
    #twilio_account_sid = "your-twilio-sid"
    #twilio_auth_token = "your-twilio-token"
    #twilio_number = "+14155238886"
  #  recipient_whatsapp = "+21698765432"  # Your number

    # Send by email
    send_email(gmail_user, gmail_app_password, "reguii1989@gmail.com", excel_file)

    # Send by WhatsApp
   # send_whatsapp_message(twilio_account_sid, twilio_auth_token, twilio_number, recipient_whatsapp, file_link)

except Exception as e:
    print(f"❌ Error sending messages: {e}")
