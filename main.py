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
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Alive - All Types")
        def do_HEAD(self): self.send_response(200); self.end_headers()
        def log_message(self, format, *args): return
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

def get_from_tab(handle, tab):
    """tab = videos / shorts / streams"""
    h = handle.replace("@","")
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/@{h}/{tab}"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        # সব videoId বের করো - প্রথমটাই লেটেস্ট
        vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', r.text)
        titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"', r.text)
        if vids:
            vid = vids[0]
            title = titles[0] if titles else "New Upload"
            return vid, title, f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print(f"Error {handle} {tab}: {e}")
    return None, None, None

def load_last():
    if os.path.exists(LAST_VIDEOS_FILE):
        try:
            with open(LAST_VIDEOS_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}
def save_last(d):
    try:
        with open(LAST_VIDEOS_FILE, 'w') as f: json.dump(d, f)
    except: pass

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ৫ টা চ্যানেলের Video, Shorts, Live আনছি...")
    for handle in CHANNEL_HANDLES:
        for tab, emoji, label in [("videos","📺","Video"), ("shorts","▶️","Shorts"), ("streams","🔴","Live")]:
            vid, title, link = get_from_tab(handle, tab)
            if link:
                await update.message.reply_text(f"{emoji} {handle} [{label}]\n{title}\n{link}")

async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    last = load_last(); new_last = last.copy()
    for handle in CHANNEL_HANDLES:
        for tab, label in [("videos","Video"), ("shorts","Shorts"), ("streams","Live")]:
            key = f"{handle}_{tab}"
            vid, title, link = get_from_tab(handle, tab)
            if not vid: continue
            if last.get(key)!= vid:
                if last.get(key) is not None: # প্রথমবার নোটিফাই না
                    try:
                        icon = "📺" if tab=="videos" else "▶️" if tab=="shorts" else "🔴 LIVE"
                        msg = f"{icon} নতুন {label}!\n{handle}\n{title}\n{link}"
                        await context.bot.send_message(chat_id=CHAT_ID, text=msg)
                    except Exception as e: print(e)
                new_last[key] = vid
    save_last(new_last)

async def post_init(application: Application):
    if CHAT_ID:
        application.job_queue.run_repeating(check_new_videos, interval=300, first=20)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Bot Started - Video+Shorts+Live")
    app.run_polling()
