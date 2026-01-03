from flask import Flask, render_template
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scraper import get_gold_price
import datetime
import os

app = Flask(__name__)

# Move this outside so every function can see it
CSV_PATH = 'data/gold_history.csv'

# Ensure the folder exists
if not os.path.exists('data'):
    os.makedirs('data')

def predict_gold():
    # Check if the file exists before reading
    if not os.path.exists(CSV_PATH):
        return "Waiting for data..."
    
    df = pd.read_csv(CSV_PATH)

    if len(df) < 2:
        return "Awaiting history..."
    
    # ML Logic
    X = np.array(range(len(df))).reshape(-1, 1)
    y = df['price'].values
    model = LinearRegression()
    model.fit(X, y)

    prediction = model.predict([[len(df)]])
    return round(prediction[0], 2)

@app.route('/')
def index():
    current = get_gold_price()
    today = datetime.date.today().strftime("%Y-%m-%d")

    # LOGIC: Check file before reading to prevent crashes
    if current:
        if not os.path.exists(CSV_PATH):
            # First time ever? Create the file!
            df_new = pd.DataFrame({'date': [today], 'price': [current]})
            df_new.to_csv(CSV_PATH, index=False)
        else:
            # File exists, check if we need to add today's entry
            df_existing = pd.read_csv(CSV_PATH)
            # Ensure we don't add duplicate entries for the same day
            if today not in df_existing['date'].values.astype(str):
                new_row = pd.DataFrame({'date': [today], 'price': [current]})
                new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)

    prediction = predict_gold()
    return render_template('index.html', current=current, prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)