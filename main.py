import os, re, requests, feedparser, asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

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

async def send_latest_videos(bot, chat_id):
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
        # লেটেস্ট ভিডিও পাঠাও
        msg = f"📺 সর্বশেষ ভিডিও\n\nচ্যানেল: {handle}\n{title}\n{link}"
        try:
            await bot.send_message(chat_id=chat_id, text=msg)
            last_data[channel_id] = video_id # সেভ করে রাখো যাতে ডাবল না আসে
        except Exception as e:
            print(e)
    save_last(last_data)

# /start দিলে এটা চলবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ ৫ টা চ্যানেলের লেটেস্ট ভিডিও আনছি...")
    await send_latest_videos(context.bot, update.effective_chat.id)
    await update.message.reply_text("✅ এরপর থেকে নতুন ভিডিও আসলেই অটো পাবে!")

async def check_loop(app):
    bot = Bot(token=BOT_TOKEN)
    while True:
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
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                    last_data[channel_id] = video_id
                except TelegramError as e:
                    print(e)
        save_last(last_data)
        await asyncio.sleep(60)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    asyncio.create_task(check_loop(app))
    print("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
