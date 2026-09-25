import os
import time
import requests
from threading import Thread
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def run_bot():
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text=✅ Bot 24h Active"
            requests.get(url)
            time.sleep(3600)
        except:
            time.sleep(10)

if __name__ == "__main__":
    Thread(target=run_bot).start()
    run_web()
