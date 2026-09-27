import os
import re
import requests
import feedparser
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# তোমার ৫ টা চ্যানেল - ID গুলো তোমার Pydroid কোড থেকে পাওয়া
CHANNEL_MAP = {
    "@thecasetoopapa": "UC-B1DgLsZVCsmn86m3diX3w",
    "@casetooop": "UCgZK0B5z3A2m5UWYvPpZcHw",
    "@casetoolive": None, # Pydroid থেকে পেলে এখানে বসাবে
    "@casetooclips": None,
    "@mrindianhacker": "UCSiDGb0MnHFGjs4E2WKvShw"
}
CHANNEL_HANDLES = list(CHANNEL_MAP.keys())

LAST_VIDEOS_FILE = "last_videos.json"

# 1. Render এর জন্য Web Server - UptimeRobot down দেখাবে না
def run_server():
    port = int(os.environ.get("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Alive - Casetoo Bot Working")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
        def log_message(self, format, *args):
            return
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# 2. Channel ID বের করা
def get_channel_id_from_handle(handle):
    # যদি MAP এ থাকে সেটা ইউজ করবে
    if CHANNEL_MAP.get(handle):
        return CHANNEL_MAP[handle]
    # না থাকলে YouTube থেকে বের করবে
    try:
        url = f"https://www.youtube.com/{handle}"
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).text
        m = re.search(r'"externalId":"(UC[^"]+)"', html)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"ID Error for {handle}: {e}")
    return None

def get_latest_video(channel_id):
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        if feed.entries:
            entry = feed.entries[0]
            return entry.id, entry.title, entry.link
    except Exception as e:
        print(f"Feed Error: {e}")
    return None, None, None

def load_last():
    if os.path.exists(LAST_VIDEOS_FILE):
        try:
            with open(LAST_VIDEOS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def save_last(data):
    try:
        with open(LAST_VIDEOS_FILE, 'w') as f:
            json.dump(data, f)
    except: pass

# 3. /start কমান্ড - একবারে ৫ টা ভিডিও দেখাবে
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ৫ টা চ্যানেলের লেটেস্ট ভিডিও আনছি...")
    for handle in CHANNEL_HANDLES:
        cid = get_channel_id_from_handle(handle)
        if not cid:
            await update.message.reply_text(f"❌ {handle} - ID পাওয়া যায়নি")
            continue
        vid_id, title, link = get_latest_video(cid)
        if link:
            await update.message.reply_text(f"📺 {handle}\n{title}\n{link}")
        else:
            await update.message.reply_text(f"⚠️ {handle} - ভিডিও পাওয়া যায়নি")

# 4. অটো নোটিফিকেশন - নতুন ভিডিও আসলে CHAT_ID তে পাঠাবে
async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    print("Checking for new videos...")
    last = load_last()
    new_last = last.copy()
    for handle in CHANNEL_HANDLES:
        cid = get_channel_id_from_handle(handle)
        if not cid: continue
        vid_id, title, link = get_latest_video(cid)
        if not vid_id: continue
        if last.get(handle)!= vid_id:
            if last.get(handle) is not None: # প্রথমবার নোটিফাই করবে না
                try:
                    msg = f"🔴 নতুন ভিডিও!\n📺 {handle}\n{title}\n{link}"
                    await context.bot.send_message(chat_id=CHAT_ID, text=msg)
                    print(f"Sent: {handle}")
                except Exception as e:
                    print(f"Send Error: {e}")
            new_last[handle] = vid_id
    save_last(new_last)

async def post_init(application: Application):
    if CHAT_ID:
        # প্রতি ৫ মিনিটে চেক করবে
        application.job_queue.run_repeating(check_new_videos, interval=300, first=20)
        print("Auto check job started")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("BOT_TOKEN missing!")
    else:
        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        app.add_handler(CommandHandler("start", start_cmd))
        print("Bot Started Polling...")
        app.run_polling()
