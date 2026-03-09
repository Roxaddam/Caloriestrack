import sqlite3
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Configuration ---
# Replace with your actual Gemini API Key
genai.configure(api_key="AIzaSyCHdS_4-L7p-xlDit3CkRHeQtDvdG1XtZQ")
model = genai.GenerativeModel('gemini-1.5-flash')

def init_db():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY, food TEXT, calories INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()

    if request.method == 'POST':
        user_input = request.form.get('food_input')
        # Use AI to parse text to calories
        prompt = f"How many calories are in '{user_input}'? Return ONLY the total number as an integer."
        response = model.generate_content(prompt)
        try:
            calories = int(response.text.strip())
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO logs (food, calories, date) VALUES (?, ?, ?)", (user_input, calories, today))
            conn.commit()
        except:
            pass # Handle AI errors gracefully
        return redirect(url_for('index'))

    # Get data for Dashboard
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(calories) FROM logs WHERE date=?", (today_str,))
    daily_total = c.fetchone()[0] or 0

    # Get Recent Logs
    c.execute("SELECT food, calories, date FROM logs ORDER BY id DESC LIMIT 5")
    recent_logs = c.fetchall()
    
    conn.close()
    return render_template('index.html', daily_total=daily_total, logs=recent_logs)

@app.route('/report')
def report():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()
    today = datetime.now()
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    c.execute("SELECT SUM(calories) FROM logs WHERE date >= ?", (week_ago,))
    weekly = c.fetchone()[0] or 0
    c.execute("SELECT SUM(calories) FROM logs WHERE date >= ?", (month_ago,))
    monthly = c.fetchone()[0] or 0
    
    conn.close()
    return render_template('index.html', weekly=weekly, monthly=monthly, show_report=True)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
    
