import time, requests, feedparser, os
BOT_TOKEN = os.environ.get("8707938321:AAHieI8e5IP0gwJX83GSIlT6Ltbw9Hc5fJc")
YOUR_CHAT_ID = os.environ.get("7825291353")
CHANNEL_ID = "UC-B1DgLsZVCsmn86m3diX3w"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
def send_msg(title, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"🔥 <b>THE CASETOO নতুন ভিডিও!</b>\n\n📌 {title}\n\n▶️ <a href='{link}'>ক্লিক করে দেখো</a>\n\n{link}"
    requests.post(url, data={"chat_id": YOUR_CHAT_ID, "text": text, "parse_mode": "HTML"})
feed = feedparser.parse(RSS_URL)
last_id = feed.entries[0].yt_videoid if feed.entries else None
if feed.entries:
    send_msg(f"✅ বট ২৪ ঘণ্টা চালু হলো! শেষ ভিডিও: {feed.entries[0].title}", feed.entries[0].link)
while True:
    try:
        feed = feedparser.parse(RSS_URL)
        if feed.entries and feed.entries[0].yt_videoid!= last_id:
            last_id = feed.entries[0].yt_videoid
            send_msg(feed.entries[0].title, feed.entries[0].link)
    except: pass
    time.sleep(300)
