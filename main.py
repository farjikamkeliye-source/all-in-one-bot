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

# Mail.tm API ka use karke Temp Mail feature
@bot.message_handler(commands=['tempmail'])
def create_temp_mail(message):
    try:
        # 1. Pehle available domain fetch karte hain
        res = requests.get("https://api.mail.tm/domains", timeout=10)
        if res.status_code != 200:
            bot.reply_to(message, "❌ Temp mail service abhi busy hai.")
            return
        
        domains = res.json().get('hydra:member', [])
        if not domains:
            bot.reply_to(message, "❌ Koi domain available nahi hai.")
            return
        
        domain = domains[0]['domain']
        
        # 2. Random email aur password create karte hain
        import random, string
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"{username}@{domain}"
        password = "Password@123"
        
        create_res = requests.post("https://api.mail.tm/accounts", json={"address": email, "password": password}, timeout=10)
        
        if create_res.status_code in [200, 201]:
            reply_msg = (
                f"📧 **Aapka Temporary Email:**\n`{email}`\n\n"
                f"🔑 **Password:** `{password}`\n\n"
                f"📥 Inbox check karne ke liye yeh command bhejein:\n"
                f"`/check {email} {password}`"
            )
            bot.reply_to(message, reply_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Email generate karne mein error aaya.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Temp Mail Inbox Check karne ke liye
@bot.message_handler(commands=['check'])
def check_mail_inbox(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Sahi format use karein:\n`/check email@domain.com password`", parse_mode="Markdown")
            return
        
        email = parts[1]
        password = parts[2]
        
        # Token generate karte hain login karke
        token_res = requests.post("https://api.mail.tm/token", json={"address": email, "password": password}, timeout=10)
        if token_res.status_code != 200:
            bot.reply_to(message, "❌ Login failed! Email ya password galat ho sakta hai.")
            return
        
        token = token_res.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Messages fetch karte hain
        msg_res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
        if msg_res.status_code == 200:
            messages = msg_res.json().get('hydra:member', [])
            if not messages:
                bot.reply_to(message, "📭 Aapka inbox khali hai! Koi naya mail nahi aaya.")
            else:
                text = "📥 **Aapke Inbox Messages:**\n\n"
                for m in messages:
                    text += f"✉️ **From:** {m['from']['address']}\n📌 **Subject:** {m['subject']}\n\n"
                bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Messages laane mein error aaya.")
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
    
