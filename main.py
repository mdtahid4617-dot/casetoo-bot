import os, time, requests, feedparser, threading
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CHANNEL_ID = "UC-B1DgLsZVCsmn86m3diX3w"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

app = Flask(__name__)
@app.route('/')
def home(): return "THE CASETOO Bot Running 24/7!"

last_video = {"id": None, "title": "", "link": ""}

def send_msg(title, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"🔥 <b>THE CASETOO নতুন ভিডিও!</b>\n\n📌 {title}\n\n▶️ <a href='{link}'>ভিডিও দেখো</a>\n\n{link}"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

# 1. YouTube চেক করবে
def youtube_checker():
    global last_video
    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        last_video = {"id": feed.entries[0].yt_videoid, "title": feed.entries[0].title, "link": feed.entries[0].link}
        send_msg(f"[Bot চালু হয়েছে] {last_video['title']}", last_video['link'])

    while True:
        time.sleep(300)
        feed = feedparser.parse(RSS_URL)
        if feed.entries and feed.entries[0].yt_videoid!= last_video["id"]:
            last_video = {"id": feed.entries[0].yt_videoid, "title": feed.entries[0].title, "link": feed.entries[0].link}
            send_msg(last_video['title'], last_video['link'])

# 2. Telegram এ /start শুনবে
def telegram_listener():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url, timeout=25).json()
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                if msg.get("text") == "/start" and str(msg.get("chat", {}).get("id")) == str(CHAT_ID):
                    # /start দিলে শেষ ভিডিওটা আবার পাঠাবে
                    if last_video["id"]:
                        send_msg(f"স্বাগতম! শেষ ভিডিও: {last_video['title']}", last_video['link'])
                    else:
                        send_msg("Bot চালু আছে, নতুন ভিডিওর জন্য অপেক্ষা করছি...", "https://youtube.com/@THECASETOO")
        except: time.sleep(5)

threading.Thread(target=youtube_checker, daemon=True).start()
threading.Thread(target=telegram_listener, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
