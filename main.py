import os
import threading
from flask import Flask
import telebot
import yt_dlp
import google.generativeai as genai

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Aapka Telegram Bot Token
TOKEN = "8309787768:AAGSFievo0aMG_s8433xSZ2txAjT8Dxn948"
bot = telebot.TeleBot(TOKEN)

# Aapki Gemini API Key yahan set kar di gayi hai
GEMINI_API_KEY = "AQ.Ab8RN6Jv4Urov_Ai7Jj0jlXzw14IHncUythBIpAII12GD6miJw"

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to Instagram & Gemini AI Bot!**\n\n"
        "Aap is bot se yeh kar sakte hain:\n"
        "🔗 **Instagram Downloader:** Video ka link seedha bhejein.\n"
        "🤖 **AI Chat:** `/ai [aapka sawal]` likhkar Gemini AI se baat karein."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Gemini AI Chat Command (/ai)
@bot.message_handler(commands=['ai'])
def chat_with_gemini(message):
    query = message.text.replace('/ai', '').strip()
    if not query:
        bot.reply_to(message, "❌ Kripya sawal bhi likhein. Example: `/ai Python kya hai?`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, "🤖 Gemini AI soch raha hai...")
    try:
        response = ai_model.generate_content(query)
        if response and response.text:
            bot.edit_message_text(response.text, message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ AI se koi jawab nahi mila.", message.chat.id, msg.message_id)
    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ AI Error: {str(e)}", message.chat.id, msg.message_id)

# Instagram Video Downloader
@bot.message_handler(func=lambda message: True)
def download_media(message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Kripya ek valid URL ya command bhejein.")
        return

    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "❌ YouTube links is bot par allowed nahi hain.")
        return

    msg = bot.reply_to(message, "🔍 Downloading media... Kripya intezaar karein.")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ Video downloaded successfully!")
        
        bot.delete_message(message.chat.id, msg.message_id)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Gemini & Downloader Bot is running...")
    bot.infinity_polling()
    
