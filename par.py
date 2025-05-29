import streamlit as st
import requests
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import re

st.set_page_config(page_title="Real Estate Scraper", layout="wide")
st.title("🏠 Tunisian Real Estate Listings Scraper")
st.markdown("Scrapes listings from **tayara.tn** and **tunisie-annonce.com**")

# --- Functions for Tayara.tn ---
def fetch_tayara(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_tayara_articles(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all("article", class_="mx-0")

def parse_tayara_article(article):
    try:
        base_url = "https://www.tayara.tn "
        a_tag = article.find('a', href=True)
        ad_url = base_url + a_tag['href'] if a_tag else None
        card = article.find('div', class_='flex-col')
        if not card:
            return {}
        title_tag = card.find('h2')
        title = title_tag.get_text(strip=True) if title_tag else None
        price_data = card.find('data', class_='font-bold')
        full_price = price_data.get_text(strip=True) if price_data else ''
        price = ''.join(filter(str.isdigit, full_price.split('DT')[0])) if 'DT' in full_price else ''
        category_span = card.find('span', class_='text-neutral-500')
        category = category_span.get_text(strip=True) if category_span else None
        prop_type = category.split(',')[0].strip() if category else None
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
        img_tag = card.find('img')
        img_alt = img_tag.get('alt', '') if img_tag else ''
        image_url = img_tag.get('src', '') if img_tag else ''
        room_match = re.search(r"S\+\d+", (title or '') + ' ' + (img_alt or ''), re.IGNORECASE)
        rooms = room_match.group(0) if room_match else None
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
        return {}

# --- Functions for Tunisie-Annonce.com ---
def fetch_tunisie_annonce(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_tunisie_annonce_rows(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all('tr', class_='Tableau1')

def parse_tunisie_annonce_row(row):
    cells = row.find_all('td')
    if len(cells) < 10:
        return {}
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
    nature_type_cell = cells[3]
    nature_tooltip = nature_type_cell.get('onmouseover', '')
    nat_match = re.search(r"<b>Nature</b> : (.+?)<br/>", nature_tooltip)
    typ_match = re.search(r"<b>Type</b> : (.+?)\"", nature_tooltip)
    nature = nat_match.group(1) if nat_match else None
    prop_type = typ_match.group(1) if typ_match else None
    desc_link = cells[7].find('a', onmouseover=True)
    title = description = link = None
    if desc_link:
        hover_text = desc_link['onmouseover']
        title_match = re.search(r"<b>(.+?)</b><br/>", hover_text)
        desc_match = re.search(r"<br/>(.+?)<br/>", hover_text)
        title = title_match.group(1) if title_match else None
        description = desc_match.group(1) if desc_match else None
        link = "http://www.tunisie-annonce.com/" + desc_link.get('href', '') if desc_link.get('href') else None
    price_cell = cells[9]
    price = price_cell.get_text(strip=True)
    price = ''.join(filter(str.isdigit, price)) if price else None
    posted_cell = cells[11]
    posted = posted_cell.get_text(strip=True) if posted_cell else None
    image_tag = cells[7].find('img', src=True)
    image_alt = image_tag.get('alt', '') if image_tag else ''
    image_url = "http://www.tunisie-annonce.com/" + image_tag['src'] if image_tag else None
    room_match = re.search(r"S\+\d+", (title or '') + ' ' + (description or '') + ' ' + (image_alt or ''), re.IGNORECASE)
    rooms = room_match.group(0) if room_match else None
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
if st.button("🔄 Start Scraping"):
    with st.spinner("Scraping tayara.tn and tunisie-annonce.com..."):
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

        df = pd.DataFrame(all_ads)
        st
