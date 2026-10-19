import os
import requests
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

def resolve_url(url):
    # حل مشكلة روابط /share/
    if "facebook.com/share" in url or "fb.watch" in url:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, allow_redirects=True, timeout=15)
            return r.url
        except:
            return url
    return url

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        # اذا البوت مو ادمن لا تعلق الناس، اعتبرو مشترك
        print(f"Check sub error: {e}")
        return True 

@bot.message_handler(commands=['start'])
def start(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك بالقناة الرسمية", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ تحققت، اشتركت", callback_data="check_sub"))
        bot.send_message(message.chat.id, 
            "يا هلا! 🔥\n\nلازم تشترك بقناتنا @BotKanal24 أول شي مشان يشتغل البوت معك:",
            reply_markup=markup)
        return

    text = "اهلا بيك بـ بوت التحميل السريع\n\nيحمل بجودة HD - بدون علامة مائية\nتيك توك | انستا | يوتيوب | فيسبوك\n\nبس ابعت الرابط وانا بجيبو بثانية"
    bot.send_message(message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "تم الاشتراك بنجاح ✅")
        bot.send_message(call.message.chat.id, "تمام اشتركت! هلا ابعت الرابط وبحملو فوراً 🚀")
    else:
        bot.answer_callback_query(call.id, "لسا ما اشتركت 😅 - تأكد انك ضغطت انضمام بالقناة", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك بالقناة", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ تحققت", callback_data="check_sub"))
        bot.send_message(message.chat.id, "❗️ لازم تشترك أولاً @BotKanal24", reply_markup=markup)
        return

    url = message.text.strip()
    if not url.startswith("http"):
        return
    
    url = resolve_url(url)
    wait = bot.reply_to(message, "⏳ عم حمل... ثانية وحدة")

    try:
        # اهم تعديل لحل خطأ 413
        ydl_opts = {
            'format': 'bestvideo[height<=720][filesize<50M]+bestaudio/best[height<=720][filesize<50M]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'max_filesize': 50 * 1024 * 1024, # 50 ميغا حد اقصى
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)
        
        # فحص الحجم بعد التحميل
        if os.path.getsize(file) > 50 * 1024 * 1024:
            os.remove(file)
            bot.edit_message_text("❌ الفيديو كبير كتير (اكتر من 50 ميغا) جرب فيديو اقصر بجودة اقل", message.chat.id, wait.message_id)
            return

        with open(file, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="تم التحميل عبر @MyDownload2026_bot ✅")
        
        os.remove(file)
        bot.delete_message(message.chat.id, wait.message_id)

    except Exception as e:
        err = str(e)
        if "Too Large" in err or "413" in err or "too large" in err.lower():
            msg = "❌ الفيديو حجمو كبير كتير، ما بقدر ابعتو عالتليجرام (الحد 50 ميغا). جرب فيديو اقصر."
        elif "facebook.com/share" in url:
            msg = "❌ رابط المشاركة هذا ما بينقرا. افتح الفيديو واضغط نسخ الرابط الحقيقي يلي فيه watch"
        else:
            msg = f"فشل: {err[:200]}"
        bot.edit_message_text(msg, message.chat.id, wait.message_id)

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode("utf-8"))])
    return "ok"

@app.route("/")
def home():
    return "Bot is running - MyDownload2026_bot"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
