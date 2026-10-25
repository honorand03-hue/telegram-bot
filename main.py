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

    # ==== هون الإضافة الجديدة اللي بدك ياها ====
    bot.send_chat_action(message.chat.id, 'upload_video') # يطلع "يرسل مقطع فيديو..."
    wait = bot.reply_to(message, "⏳ عم حمل... ثانية وحدة")
    bot.send_chat_action(message.chat.id, 'upload_video') # مرة تانية مشان يضل طالع
    
    try:
        ydl_opts = {
            'format': 'bestvideo[height<=720][filesize<50M]+bestaudio/best[height<=720][filesize<50M]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'max_filesize': 50 * 1024 * 1024,
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)
        
        if os.path.getsize(file) > 50 * 1024 * 1024:
            os.remove(file)
            bot.edit_message_text("❌ الفيديو كبير كتير (اكتر من 50 ميغا) جرب فيديو اقصر بجودة اقل", message.chat.id, wait.message_id)
            return

        # ==== هون كمان قبل الارسال ====
        bot.send_chat_action(message.chat.id, 'upload_video')
        
        with open(file, 'rb') as f:
            bot.send_video(
                message.chat.id, 
                f, 
                caption="تم التحميل عبر @MyDownload2026_bot ✅",
                supports_streaming=True # هاد يخليه يطلع كمقطع مرئي مو كملف
            )
        
        os.remove(file)
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception as e:
        err = str(e)
        if "Too Large" in err or "413" in err or "too large" in err.lower():
            msg = "❌ الفيديو حجمو كبير كتير، ما بقدر ابعتو عالتليجرام (الحد 50 ميغا). جرب فيديو اقصر."
        else:
            msg = f"فشل: {err[:200]}"
        bot.edit_message_text(msg, message.chat.id, wait.message_id)
