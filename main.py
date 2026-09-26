import os, re, requests, feedparser, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHANNEL_HANDLES = [
    "@THECASETOO",
    "@casetooop",
    "@casetoolive",
    "@casetooclips",
    "@mrindianhacker",
]

LAST_FILE = "last_videos.txt"

# Render এর জন্য Dummy Web Server - এটা থাকলে No open ports Error আসবে না
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Running!")
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

def get_channel_id(handle):
    try:
        url = f"https://www.youtube.com/{handle}"
        r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        m = re.search(r'"channelId":"(UC[^"]+)"', r.text)
        if m: return m.group(1)
        m2 = re.search(r'"browseId":"(UC[^"]+)"', r.text)
        if m2: return m2.group(1)
    except: pass
    return None

def load_last():
    if not os.path.exists(LAST_FILE): return {}
    try:
        with open(LAST_FILE, "r") as f:
            data = {}
            for line in f:
                if ":" in line:
                    k,v = line.strip().split(":",1)
                    data[k]=v
            return data
    except: return {}

def save_last(data):
    with open(LAST_FILE, "w") as f:
        for k,v in data.items():
            f.write(f"{k}:{v}\n")

async def send_latest_videos(context, chat_id):
    last_data = load_last()
    for handle in CHANNEL_HANDLES:
        channel_id = get_channel_id(handle)
        if not channel_id: continue
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        if not feed.entries: continue
        latest = feed.entries[0]
        video_id = latest.yt_videoid
        title = latest.title
        link = latest.link
        msg = f"📺 সর্বশেষ ভিডিও\n\nচ্যানেল: {handle}\n{title}\n{link}"
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
            last_data[channel_id] = video_id
        except Exception as e:
            print(e)
    save_last(last_data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ৫ টা চ্যানেলের লেটেস্ট ভিডিও আনছি...")
    await send_latest_videos(context, update.effective_chat.id)

async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    last_data = load_last()
    for handle in CHANNEL_HANDLES:
        channel_id = get_channel_id(handle)
        if not channel_id: continue
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        if not feed.entries: continue
        latest = feed.entries[0]
        video_id = latest.yt_videoid
        last_id = last_data.get(channel_id)
        if last_id and video_id!= last_id:
            title = latest.title
            link = latest.link
            msg = f"🔔 নতুন ভিডিও!\n\nচ্যানেল: {handle}\n{title}\n{link}"
            try:
                await context.bot.send_message(chat_id=context.job.chat_id, text=msg)
                last_data[channel_id] = video_id
            except Exception as e:
                print(e)
    save_last(last_data)

async def post_init(application):
    if CHAT_ID:
        application.job_queue.run_repeating(check_new_videos, interval=60, first=10, chat_id=CHAT_ID)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.post_init = post_init
    print("Bot started...")
    app.run_polling()
