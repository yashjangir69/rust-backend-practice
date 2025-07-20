import json
import time
import telebot
from datetime import datetime, time as dt_time
from keep_alive import keep_alive

# === CONFIG ===
BOT_TOKEN = '7614609361:AAFhaKMZP0X_VXItWFDDL-d30YKaiUxxe0M'  # 🔁 Replace with your actual bot token
GROUP_ID = -1002862711974           # 🔁 Replace with your group ID
THREAD_ID = 2                       # 🔁 Replace with topic/thread ID (or remove this if not using topics)

WORDS_PER_BATCH = 5                # 🔁 Number of vocab per batch
INTERVAL_SECONDS = 60     # ⏰ 2 hours = 7200 seconds
ALLOWED_START = dt_time(0, 0)      # Start at 7:00 AM
ALLOWED_END = dt_time(23, 0)       # Stop after 11:00 PM

VOCAB_FILE = 'vocab.json'
USED_WORDS_FILE = 'used_words.json'

bot = telebot.TeleBot(BOT_TOKEN)

# === Vocab Handling ===

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

# === Bot Command ===

@bot.message_handler(commands=['getid'])
def get_thread_id(message):
    if message.is_topic_message:
        thread_id = message.message_thread_id
        bot.reply_to(message,
                     f"🧵 This topic's thread ID is:\n`{thread_id}`",
                     parse_mode="Markdown")
    else:
        bot.reply_to(message, "❗ Please send this command inside a topic.")

# === Auto Vocab Sending Loop ===

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

            print(f"✅ Sent vocab batch at {datetime.now()} — sleeping for 2 hours.")
            time.sleep(INTERVAL_SECONDS)
        else:
            print(f"⏳ Outside allowed hours — sleeping for 10 mins. Time: {datetime.now()}")
            time.sleep(600)

# === MAIN ===

if __name__ == "__main__":
    print("✅ Bot is running...")
    keep_alive()
    # Start vocab loop in background using Telebot's polling loop
    import threading
    threading.Thread(target=run_vocab_scheduler, daemon=True).start()

    bot.infinity_polling()
