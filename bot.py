import os
import telebot
import yt_dlp
import glob
import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_DIR = "/tmp/downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
user_links = {}

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Bhai, mujhe koi bhi YouTube, Insta, ya FB ka link bhejo.\nMain tumhe MP3 ya MP4 me download karke dunga.")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def ask_format(message):
    url = message.text.strip()
    user_links[message.chat.id] = url
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio"),
        InlineKeyboardButton("🎬 Video (MP4)", callback_data="video")
    )
    bot.reply_to(message, "Tumhe kya chahiye? Niche select karo:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    if not url:
        bot.answer_callback_query(call.id, "Link expire ho gaya.")
        return
    if call.data == "audio":
        bot.edit_message_text("⏳ Audio Download ho raha hai...", chat_id, call.message.message_id)
        download_media(chat_id, url, 'mp3')
    elif call.data == "video":
        markup = InlineKeyboardMarkup()
        markup.row_width = 3
        markup.add(
            InlineKeyboardButton("144p", callback_data="v_144"),
            InlineKeyboardButton("360p", callback_data="v_360"),
            InlineKeyboardButton("480p", callback_data="v_480")
        )
        bot.edit_message_text("Quality select karo:", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("v_"):
        quality = call.data.split("_")[1]
        bot.edit_message_text(f"⏳ Video ({quality}) Download ho raha hai...", chat_id, call.message.message_id)
        download_media(chat_id, url, 'mp4', quality)
    bot.answer_callback_query(call.id)

def download_media(chat_id, url, format_type, quality=None):
    bot.send_chat_action(chat_id, 'upload_document')
    ydl_opts = {'outtmpl': DOWNLOAD_DIR + '%(title)s.%(ext)s', 'quiet': True, 'noplaylist': True}
    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio[filesize<15M]/bestaudio',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
        })
    else:
        if quality == '144': fmt = 'bestvideo[height<=144][filesize<18M]+bestaudio/best[height<=144]/best'
        elif quality == '360': fmt = 'bestvideo[height<=360][filesize<18M]+bestaudio/best[height<=360]/best'
        else: fmt = 'bestvideo[height<=480][filesize<18M]+bestaudio/best[height<=480]/best'
        ydl_opts.update({'format': fmt, 'merge_output_format': 'mp4'})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base_name = os.path.splitext(filename)[0]
            possible_files = glob.glob(base_name + '.*')
            if possible_files: filename = possible_files[0]
        if os.path.getsize(filename) > 20 * 1024 * 1024:
            os.remove(filename)
            bot.send_message(chat_id, "❌ File 20MB se badi hai.")
            return
        bot.send_message(chat_id, "📤 Upload ho raha hai...")
        with open(filename, 'rb') as f:
            caption = f"✅ {info.get('title')[:50]}..."
            if format_type == 'mp3': bot.send_audio(chat_id, f, caption=caption, timeout=300)
            else: bot.send_video(chat_id, f, caption=caption, timeout=300)
        os.remove(filename)
        del user_links[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")

threading.Thread(target=run_flask).start()
print("Bot is running...")
bot.remove_webhook()
bot.infinity_polling()
