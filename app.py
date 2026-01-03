from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scraper import get_gold_price, get_30_day_history
import datetime
import os

app = Flask(__name__)
CSV_PATH = 'data/gold_history.csv'

def get_valid_cached_price(today_str):
    """Ensures we always get a numeric price, never NaN."""
    fallback_price = 8200.0  # Emergency backup
    
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df.dropna(subset=['price']) # REMOVE BROKEN DATA
        
        if not df.empty:
            # Check if we already have today's price
            today_data = df[df['date'] == today_str]
            if not today_data.empty:
                return float(today_data.iloc[0]['price'])
            fallback_price = float(df.iloc[-1]['price'])

    # If not in CSV or missing today, try to scrape
    new_price = get_gold_price()
    if new_price:
        df_new = pd.DataFrame({'date': [today_str], 'price': [new_price]})
        if not os.path.exists(CSV_PATH):
            df_new.to_csv(CSV_PATH, index=False)
        else:
            df_new.to_csv(CSV_PATH, mode='a', header=False, index=False)
        return new_price
        
    return fallback_price

def predict_gold():
    if not os.path.exists(CSV_PATH): return None, None
    df = pd.read_csv(CSV_PATH)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['price']).sort_values(by='date')
    
    if len(df) < 2: return None, None # AI needs at least 2 days to see a trend

    start_date = df['date'].min()
    df['days_since'] = (df['date'] - start_date).dt.days
    X = df[['days_since']].values
    y = df['price'].values
    return LinearRegression().fit(X, y), start_date

@app.route('/', methods=['GET', 'POST'])
def index():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    current = get_valid_cached_price(today_str)
    
    model, start_date = predict_gold()
    
    # Load data for chart
    df = pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame()
    if not df.empty:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df.dropna(subset=['price']).sort_values(by='date')

    user_grams = float(request.form.get('grams', 1)) if request.method == 'POST' else 1.0
    target_date_str = request.form.get('target_date', today_str) if request.method == 'POST' else today_str
    
    labels, actual_values, trend_values = [], [], []
    display_prediction = current * user_grams

    if not df.empty:
        labels = df['date'].tolist()
        actual_values = df['price'].tolist()

        if model and start_date:
            # Calculate Trend
            X_hist = (pd.to_datetime(df['date']) - start_date).dt.days.values.reshape(-1, 1)
            trend_values = [round(v, 2) for v in model.predict(X_hist)]

            # Calculate Prediction
            target_date_obj = datetime.datetime.strptime(target_date_str, "%Y-%m-%d")
            days_diff = (target_date_obj - start_date).days
            price_pred = model.predict([[days_diff]])[0]
            display_prediction = round(price_pred * user_grams, 2)
            
            # Add prediction to chart
            labels.append(target_date_str)
            actual_values.append(None)
            trend_values.append(round(price_pred, 2))

    return render_template('index.html', current=current, prediction=display_prediction, 
                           labels=labels, actual=actual_values, trend=trend_values,
                           grams=user_grams, target_date=target_date_str)

@app.route('/scrape-history', methods=['POST'])
def scrape_history():
    new_data = get_30_day_history()
    if new_data:
        df_new = pd.DataFrame(new_data)
        if os.path.exists(CSV_PATH):
            df_old = pd.read_csv(CSV_PATH)
            df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=['date'], keep='last')
            df_combined.sort_values(by='date').to_csv(CSV_PATH, index=False)
        else:
            df_new.sort_values(by='date').to_csv(CSV_PATH, index=False)
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('data'): os.makedirs('data')
    app.run(debug=True)