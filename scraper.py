import requests
from bs4 import BeautifulSoup
import re
import datetime

def get_gold_price():
    url = "https://goldpricez.com/ph/gram"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # 20 second timeout is usually enough
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r"24-Karat.*?([\d,]+\.\d{2})", text)
        if match:
            price_str = match.group(1).replace(',', '')
            return float(price_str)
    except Exception as e:
        print(f"Scraper Error: {e}")
    return None # Return None if internet/site is down

def get_30_day_history():
    url = "https://goldpricez.com/ph/gram/history"
    headers = {"User-Agent": "Mozilla/5.0"}
    history_data = []
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'history_table'}) or soup.find('table')
        if table:
            rows = table.find_all('tr')[1:] 
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    try:
                        date_obj = datetime.datetime.strptime(cols[0].text.strip(), "%d %b %Y")
                        price_raw = cols[1].text.replace('PHP', '').replace(',', '').strip()
                        history_data.append({'date': date_obj.strftime("%Y-%m-%d"), 'price': float(price_raw)})
                    except: continue
    except: pass
    return history_data