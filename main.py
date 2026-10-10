import os, re, requests, feedparser, threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHANNEL_HANDLES = ["@thecasetoopapa", "@casetooop", "@casetoolive", "@casetooclips", "@mrindianhacker"]
LAST_VIDEOS_FILE = "last_videos.json"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Bot is Alive - Casetoo Bot Working")
        def do_HEAD(self):
            self.send_response(200); self.end_headers()
        def log_message(self, format, *args): return
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

def get_channel_id_from_handle(handle):
    h = handle.replace("@","")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    urls = [f"https://www.youtube.com/@{h}", f"https://www.youtube.com/c/{h}", f"https://www.youtube.com/{handle}"]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            # 2 ভাবে ID খোঁজার চেষ্টা
            m1 = re.search(r'"channelId":"(UC[^"]+)"', r.text)
            if m1: return m1.group(1)
            m2 = re.search(r'"externalId":"(UC[^"]+)"', r.text)
            if m2: return m2.group(1)
            m3 = re.search(r'/channel/(UC[0-9A-Za-z_-]{22})', r.text)
            if m3: return m3.group(1)
        except Exception as e:
            print(f"ID Error {handle} at {url}: {e}")
    return None

def get_latest_video(channel_id):
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        # feedparser এর জন্য header দরকার নেই, সরাসরি parse
        feed = feedparser.parse(feed_url)
        if feed.entries:
            entry = feed.entries[0]
            return entry.id, entry.title, entry.link
        else:
            print(f"Feed empty for {channel_id}")
    except Exception as e:
        print(f"Feed Error {channel_id}: {e}")
    return None, None, None

def load_last():
    if os.path.exists(LAST_VIDEOS_FILE):
        try:
            with open(LAST_VIDEOS_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}
def save_last(data):
    try:
        with open(LAST_VIDEOS_FILE, 'w') as f: json.dump(data, f)
    except: pass

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ৫ টা চ্যানেলের লেটেস্ট ভিডিও আনছি...")
    for handle in CHANNEL_HANDLES:
        cid = get_channel_id_from_handle(handle)
        print(f"{handle} -> {cid}")
        if not cid:
            await update.message.reply_text(f"❌ {handle} - ID পাওয়া যায়নি, ইউজারনেম চেক করো")
            continue
        vid_id, title, link = get_latest_video(cid)
        if link:
            await update.message.reply_text(f"📺 {handle}\n{title}\n{link}")
        else:
            await update.message.reply_text(f"⚠️ {handle} - ভিডিও পাওয়া যায়নি (ID: {cid})")

async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    last = load_last(); new_last = last.copy()
    for handle in CHANNEL_HANDLES:
        cid = get_channel_id_from_handle(handle)
        if not cid: continue
        vid_id, title, link = get_latest_video(cid)
        if not vid_id: continue
        if last.get(handle)!= vid_id:
            if last.get(handle) is not None:
                try:
                    msg = f"🔴 নতুন ভিডিও!\n📺 {handle}\n{title}\n{link}"
                    await context.bot.send_message(chat_id=CHAT_ID, text=msg)
                except Exception as e: print(f"Send Error: {e}")
            new_last[handle] = vid_id
    save_last(new_last)

async def post_init(application: Application):
    if CHAT_ID:
        application.job_queue.run_repeating(check_new_videos, interval=300, first=20)
        print("Auto check job started")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Bot Started Polling...")
    app.run_polling()
