import requests
from bs4 import BeautifulSoup
import datetime
import os


def get_gold_price():
    url = "https://goldpricez.com/ph/gram"
    headers = {"User-Agent" : "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        price_element = soup.find("div", {"class" : "gold_price_gram_php"})
        if not price_element:
            price_element = soup.find("b")

        price_text = price_element.get_text().replace(',', ' ').strip()
        return float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))

    except Exception as e:
        print("Error:", e)
        return None

def save_to_csv(price):
    file_path = 'data/gold_history.csv'
    date = datetime.date.today().strftime("%Y-%-%d")

    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            f.write("date,price\n")
    
    with open(file_path, 'a') as f:
        f.write(f"{date}, {price} \n")