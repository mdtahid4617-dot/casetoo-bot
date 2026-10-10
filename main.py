import os, re, requests, threading, json
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
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Alive")
        def do_HEAD(self): self.send_response(200); self.end_headers()
        def log_message(self, format, *args): return
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

def get_latest_video_direct(handle):
    h = handle.replace("@","")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    urls = [f"https://www.youtube.com/@{h}/videos", f"https://www.youtube.com/c/{h}/videos"]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            # পেজ থেকে সরাসরি videoId বের করা
            m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', r.text)
            if m:
                vid = m.group(1)
                # টাইটেল বের করা
                tm = re.search(r'"title":{"runs":\[{"text":"([^"]+)"', r.text)
                title = tm.group(1) if tm else "New Video"
                return vid, title, f"https://www.youtube.com/watch?v={vid}"
        except Exception as e:
            print(f"Error {handle}: {e}")
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
        vid_id, title, link = get_latest_video_direct(handle)
        if link:
            await update.message.reply_text(f"📺 {handle}\n{title}\n{link}")
        else:
            await update.message.reply_text(f"⚠️ {handle} - ভিডিও পাওয়া যায়নি, চ্যানেল প্রাইভেট বা ইউজারনেম ভুল")

async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    last = load_last(); new_last = last.copy()
    for handle in CHANNEL_HANDLES:
        vid_id, title, link = get_latest_video_direct(handle)
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

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Bot Started...")
    app.run_polling()
