from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from openai import OpenAI
from collections import defaultdict
import json
import os

# ================== НАСТРОЙКИ ==================
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID"))
MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
Ты мой личный ассистент.
Отвечай кратко, по делу.
Помогай планировать, думать и принимать решения.
"""

MEMORY_FILE = "memory.json"
# ===============================================

client = OpenAI(api_key=OPENAI_KEY)
history = defaultdict(list)

# --------- ЗАГРУЗКА ПАМЯТИ ---------
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        history.update(json.load(f))

# --------- СОХРАНЕНИЕ ПАМЯТИ ---------
def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# --------- ПРОВЕРКА ДОСТУПА ---------
def is_owner(update):
    return update.effective_user.id == OWNER_ID

# --------- ОБРАБОТКА СООБЩЕНИЙ ---------
async def handle_message(update, context):
    if not is_owner(update):
        return

    user_id = str(update.effective_user.id)
    text = update.message.text

    history[user_id].append({"role": "user", "content": text})
    history[user_id] = history[user_id][-12:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[user_id]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    answer = response.choices[0].message.content
    history[user_id].append({"role": "assistant", "content": answer})
    save_memory()

    await update.message.reply_text(answer)

# --------- КОМАНДЫ ---------
async def clear(update, context):
    if not is_owner(update):
        return
    history[str(OWNER_ID)] = []
    save_memory()
    await update.message.reply_text("🧹 Память очищена")

async def start(update, context):
    if not is_owner(update):
        return
    await update.message.reply_text("🤖 Личный ассистент запущен")

# --------- ЗАПУСК ---------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()