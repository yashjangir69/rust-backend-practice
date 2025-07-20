import os
import json
import time
import telebot
import threading
from datetime import datetime, time as dt_time
from flask import Flask

# === CONFIG ===
BOT_TOKEN = os.environ.get("BOT_API_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))  # Note: env vars are strings, cast to int
THREAD_ID = int(os.environ.get("THREAD_ID", 2))  # Optional thread/topic

WORDS_PER_BATCH = 5
INTERVAL_SECONDS = 60  # 1 min (for testing)
ALLOWED_START = dt_time(0, 0)
ALLOWED_END = dt_time(23, 0)

VOCAB_FILE = 'vocab.json'
USED_WORDS_FILE = 'used_words.json'

bot = telebot.TeleBot(BOT_TOKEN)

# === Vocab Utilities ===
def load_vocab():
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_used_words():
    try:
        with open(USED_WORDS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_used_words(used_words):
    with open(USED_WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(used_words), f, ensure_ascii=False)

def format_vocab_list(vocab_list):
    return "\n\n".join([
        f"📑 *{item['Word']}*\n👉 Meaning:\n_{item['Meaning']}_\n👉 Hindi:\n{item['Hindi']}"
        for item in vocab_list
    ])

# === Telegram Bot Command ===
@bot.message_handler(commands=['getid'])
def get_thread_id(message):
    if message.is_topic_message:
        thread_id = message.message_thread_id
        bot.reply_to(message,
                     f"🧵 This topic's thread ID is:\n`{thread_id}`",
                     parse_mode="Markdown")
    else:
        bot.reply_to(message, "❗ Please send this command inside a topic.")

# === Vocab Scheduler ===
def run_vocab_scheduler():
    while True:
        now = datetime.now().time()

        if ALLOWED_START <= now <= ALLOWED_END:
            vocab = load_vocab()
            used = load_used_words()
            remaining = [v for v in vocab if v['Word'] not in used]

            if not remaining:
                bot.send_message(GROUP_ID,
                                 "✅ All vocabulary words have been sent.",
                                 parse_mode="Markdown",
                                 message_thread_id=THREAD_ID)
                break

            batch = remaining[:WORDS_PER_BATCH]
            used.update([item['Word'] for item in batch])
            save_used_words(used)

            message = format_vocab_list(batch)
            bot.send_message(GROUP_ID,
                             message,
                             parse_mode="Markdown",
                             message_thread_id=THREAD_ID)

            print(f"✅ Sent vocab batch at {datetime.now()} — sleeping {INTERVAL_SECONDS}s.")
            time.sleep(INTERVAL_SECONDS)
        else:
            print(f"⏳ Outside allowed hours — sleeping for 10 mins. Time: {datetime.now()}")
            time.sleep(600)

# === Flask server (to keep alive) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# === Main Entry ===
if __name__ == "__main__":
    print("✅ Starting bot service on Render...")
    
    # Start background web server
    threading.Thread(target=run_web).start()
    
    # Start vocab scheduler in another thread
    threading.Thread(target=run_vocab_scheduler, daemon=True).start()
    
    # Start receiving bot updates
    bot.infinity_polling()
