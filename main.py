import os
import requests
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultVideo
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

def resolve_url(url):
    if "facebook.com/share" in url or "fb.watch" in url:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
            return r.url
        except:
            return url
    return url

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return True

@bot.inline_handler(func=lambda query: True)
def inline_query_handler(inline_query):
    text = inline_query.query.strip()
    if not text.startswith("http"): return
    try:
        url = resolve_url(text)
        ydl_opts = {'format': 'best[height<=720]','quiet': True,'noplaylist': True,'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            thumb = info.get('thumbnail', '')
            title = info.get('title', 'فيديو')[:50]
            if not video_url: return
            result = InlineQueryResultVideo(id="1", video_url=video_url, mime_type="video/mp4", thumb_url=thumb, title=f"✅ {title}", caption="تم التحميل عبر @MyDownload2026_bot", description="اضغط لإرسال الفيديو")
            bot.answer_inline_query(inline_query.id, [result], cache_time=1)
    except Exception as e:
        print(f"Inline error: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك بالقناة الرسمية", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ تحققت، اشتركت", callback_data="check_sub"))
        bot.send_message(message.chat.id, "يا هلا! 🔥\nلازم تشترك بقناتنا @BotKanal24 أول شي:", reply_markup=markup)
        return
    bot.send_message(message.chat.id, "اهلا بيك بـ بوت التحميل السريع\nيحمل HD - بدون علامة مائية\nتيك توك | انستا | يوتيوب | فيسبوك\n\n💡 **جديد:** رح ابعتلك الفيديو مع زر تحويله لموسيقى MP3 فوراً!")

@bot.callback_query_handler(func=lambda call: True)
def all_callbacks(call):
    if call.data == "check_sub":
        if is_subscribed(call.from_user.id):
            bot.answer_callback_query(call.id, "تم ✅")
            bot.send_message(call.message.chat.id, "تمام! ابعت الرابط 🚀")
        else:
            bot.answer_callback_query(call.id, "لسا ما اشتركت 😅", show_alert=True)
        return

    # زر تحويل لموسيقى
    if call.data.startswith("audio|"):
        file_path = call.data.split("|")[1]
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "الملف انحذف، ابعت الرابط مرة تانية")
            return
        bot.answer_callback_query(call.id, "⏳ عم حوله لموسيقى...")
        bot.send_chat_action(call.message.chat.id, 'upload_audio')
        try:
            base = os.path.splitext(file_path)[0]
            mp3_file = base + ".mp3"
            os.system(f'ffmpeg -y -i "{file_path}" -vn -ab 128k "{mp3_file}"')
            with open(mp3_file, 'rb') as f:
                bot.send_audio(call.message.chat.id, f, title="Audio")
            os.remove(mp3_file)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"خطأ بالتحويل: {e}")

@bot.message_handler(func=lambda m: True)
def handle(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك بالقناة", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ تحققت", callback_data="check_sub"))
        bot.send_message(message.chat.id, "❗️ لازم تشترك أولاً @BotKanal24", reply_markup=markup)
        return
    url = message.text.strip()
    if not url.startswith("http"): return
    url = resolve_url(url)
    
    bot.send_chat_action(message.chat.id, 'upload_video')
    wait = bot.reply_to(message, "⏳ عم حمل... ثانية وحدة")
    
    try:
        ydl_opts = {
            'format': 'bestvideo[height<=720][filesize<50M]+bestaudio/best[height<=720][filesize<50M]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s','quiet': True,'noplaylist': True,
            'max_filesize': 50 * 1024 * 1024,
            'http_headers': {'User-Agent': 'Mozilla/5.0'},'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎵 حول لموسيقى MP3", callback_data=f"audio|{file}"))
        
        with open(file, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="✅ تم - اضغط تحت لتحويله لموسيقى", supports_streaming=True, reply_markup=markup)
        bot.delete_message(message.chat.id, wait.message_id)
        # لا تحذف الملف فوراً مشان زر الموسيقى
    except Exception as e:
        err = str(e)
        bot.edit_message_text(f"فشل: {err[:200]}", message.chat.id, wait.message_id)

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode("utf-8"))])
    return "ok"

@app.route("/")
def home():
    return "Bot is running - MyDownload2026_bot"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
