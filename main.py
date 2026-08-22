import os
import threading
from flask import Flask
import requests
import telebot
import yt_dlp

# Flask app taaki Render ka port error na aaye
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Aapka Telegram Bot Token
TOKEN = "8852793555:AAHeGoB66uD-R0_J37z4KOsBsunag2_Xwd4"
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
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        mails = response.json()
        if mails:
            email = mails[0]
            bot.reply_to(message, f"📧 **Aapka Temporary Email:**\n`{email}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Email generate karne mein error aaya.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['ai'])
def chat_with_ai(message):
    query = message.text.replace('/ai', '').strip()
    if not query:
        bot.reply_to(message, "❌ Kripya sawal bhi likhein. Example: `/ai Python kya hai?`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, "🤖 AI soch raha hai...")
    try:
        r = requests.get(f"https://api.popcat.xyz/chatbot?msg={requests.utils.quote(query)}")
        res = r.json()
        if 'response' in res:
            bot.edit_message_text(res['response'], message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ AI se jawab nahi mila.", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

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
    # Web server ko background thread mein chalana taaki port error na aaye
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Multi-tool Bot is running...")
    bot.infinity_polling()
