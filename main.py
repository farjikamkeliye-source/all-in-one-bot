import os
import requests
import telebot
import yt_dlp

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

# 1. Temp Mail Feature (/tempmail)
@bot.message_handler(commands=['tempmail'])
def create_temp_mail(message):
    try:
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        mails = response.json()
        if mails:
            email = mails[0]
            bot.reply_to(message, f"📧 **Aapka Temporary Email:**\n`{email}`\n\n(Is par aaye mails check karne ke liye `/checkmail {email}` likhein)", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Email generate karne mein error aaya.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# 2. Check Temp Mail Inbox (/checkmail)
@bot.message_handler(commands=['checkmail'])
def check_temp_mail(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kripya email bhi likhein. Example: `/checkmail abc@1secmail.com`", parse_mode="Markdown")
            return
        
        email = parts[1]
        login, domain = email.split('@')
        response = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}")
        messages = response.json()
        
        if messages:
            msg_list = "📥 **Aapke Inbox Messages:**\n\n"
            for m in messages[:3]:
                msg_list += f"✉️ **From:** {m['from']}\n📌 **Subject:** {m['subject']}\n🆔 **ID:** {m['id']}\n\n"
            msg_list += "Pura message padhne ke liye `/readmail email@domain.com id` likhein."
            bot.reply_to(message, msg_list, parse_mode="Markdown")
        else:
            bot.reply_to(message, "📭 Inbox khali hai! Koi naya mail nahi aaya.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# 3. AI Chat Feature (/ai)
@bot.message_handler(commands=['ai'])
def chat_with_ai(message):
    query = message.text.replace('/ai', '').strip()
    if not query:
        bot.reply_to(message, "❌ Kripya sawal bhi likhein. Example: `/ai Python kya hai?`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, "🤖 AI soch raha hai...")
    try:
        # Free public AI API use kar rahe hain
        r = requests.get(f"https://api.popcat.xyz/chatbot?msg={requests.utils.quote(query)}")
        res = r.json()
        if 'response' in res:
            bot.edit_message_text(res['response'], message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ AI se jawab nahi mila.", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

# 4. Media Downloader (Instagram / Links)
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

print("Multi-tool Bot is running...")
bot.infinity_polling()
