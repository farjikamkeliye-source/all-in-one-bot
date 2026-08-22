import os
import threading
from flask import Flask
import requests
import telebot
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

TOKEN = "8309787768:AAGSFievo0aMG_s8433xSZ2txAjT8Dxn948"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to All-in-One Bot!**\n\n"
        "Aap is bot se yeh sab kar sakte hain:\n"
        "🔗 **Instagram Downloader:** Seedha link bhejein.\n"
        "🤖 **AI Chat:** `/ai [aapka sawal]` likhkar puchein.\n"
        "📧 **Temp Mail:** `/tempmail` likhkar fake email banayein."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['tempmail'])
def create_temp_mail(message):
    try:
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=10)
        if response.status_code == 200:
            mails = response.json()
            if mails:
                email = mails[0]
                bot.reply_to(message, f"📧 **Aapka Temporary Email:**\n`{email}`", parse_mode="Markdown")
                return
        bot.reply_to(message, "❌ Filhaal Temp Mail service response nahi de rahi. Thodi der baad try karein.")
    except Exception as e:
        bot.reply_to(message, "❌ Temp mail generate karne mein error aaya. API down ho sakti hai.")

@bot.message_handler(commands=['ai'])
def chat_with_ai(message):
    query = message.text.replace('/ai', '').strip()
    if not query:
        bot.reply_to(message, "❌ Kripya sawal bhi likhein. Example: `/ai Python kya hai?`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, "🤖 AI soch raha hai...")
    try:
        # Better and stable AI endpoint
        r = requests.get(f"https://api.popcat.xyz/chatbot?msg={requests.utils.quote(query)}", timeout=10)
        if r.status_code == 200:
            res = r.json()
            if 'response' in res:
                bot.edit_message_text(res['response'], message.chat.id, msg.message_id)
                return
        bot.edit_message_text("❌ AI server busy hai, kripya thodi der baad try karein.", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ Request timed out! AI server respond nahi kar raha.", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda message: True)
def download_media(message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Kripya ek valid URL ya command bhejein.")
        return

    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "❌ YouTube links is bot par band hain. Kripya Instagram link bhejein.")
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
    
    print("Multi-tool Bot is running...")
    bot.infinity_polling()
    
