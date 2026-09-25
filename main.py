import os
import time
import requests
import feedparser
from flask import Flask
import threading

# টোকেন GitHub এ থাকবে না, Render এর Environment থেকে আসবে
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: BOT_TOKEN বা CHAT_ID Render এ সেট করা নেই!")

CHANNEL_ID = "UC-B1DgLsZVCsmn86m3diX3w"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

app = Flask(__name__)

@app.route('/')
def home():
    return "THE CASETOO Bot is Running 24/7!"

def send_msg(title, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"🔥 <b>THE CASETOO নতুন ভিডিও দিয়েছে!</b>\n\n📌 {title}\n\n▶️ <a href='{link}'>এখানে ক্লিক করে ভিডিও দেখো</a>\n\n{link}"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"Message Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def run_bot():
    print(f"Checking Channel: {CHANNEL_ID}")
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("এখনো ভিডিও পাওয়া যায়নি")
            return

        last_id = feed.entries[0].yt_videoid
        print(f"Last Video: {feed.entries[0].title}")

        # টেস্ট মেসেজ - বট চালু হলেই তুমি পাবে
        send_msg(f"[TEST] {feed.entries[0].title}", feed.entries[0].link)

        while True:
            time.sleep(300) # 5 মিনিট পর পর চেক
            try:
                feed = feedparser.parse(RSS_URL)
                if feed.entries and feed.entries[0].yt_videoid!= last_id:
                    last_id = feed.entries[0].yt_videoid
                    send_msg(feed.entries[0].title, feed.entries[0].link)
                    print("নতুন ভিডিও পাঠানো হয়েছে!")
            except Exception as e:
                print(e)
    except Exception as e:
        print(f"Bot Start Error: {e}")

# বট ব্যাকগ্রাউন্ডে চলবে
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
