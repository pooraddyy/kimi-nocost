<div align="center">

<h1>kimi-nocost Demo</h1>
<p>Building a Telegram bot powered by Kimi AI — with image & file upload support</p>

<a href="https://t.me/pythontodayz"><img src="https://img.shields.io/badge/Telegram-%40pythontodayz-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"/></a>

</div>

---

## Prerequisites

```bash
pip install kimi-nocost python-telegram-bot
```

---

## What You Need

| Item | Where to get it |
|------|----------------|
| **Kimi token** | [kimi.moonshot.cn](https://kimi.moonshot.cn) → DevTools → Network → `Authorization: Bearer <token>` |
| **Telegram bot token** | [@BotFather](https://t.me/BotFather) → `/newbot` |

---

## Full Telegram Bot

Save this as `bot.py` and run it:

```python
import io
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from kimi_nocost import KimiClient, Models

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
KIMI_TOKEN = os.environ["KIMI_TOKEN"]

user_clients: dict[int, KimiClient] = {}


def get_client(user_id: int) -> KimiClient:
    if user_id not in user_clients:
        user_clients[user_id] = KimiClient(token=KIMI_TOKEN)
    return user_clients[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm powered by Kimi AI.\n\n"
        "Send any message, photo, or file and I'll respond.\n\n"
        "Commands:\n"
        "/start — show this message\n"
        "/new — start a fresh conversation\n"
        "/search <query> — ask with web search enabled\n"
        "/model <name> — switch model (kimi, k2d6, k2d6-thinking, k2d6-agent)"
    )


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = get_client(update.effective_user.id)
    client.new_chat()
    await update.message.reply_text("New conversation started.")


async def switch_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = " ".join(context.args).strip()
    if not model:
        await update.message.reply_text(
            "Usage: /model <name>\n"
            "Available: kimi, k1, k2d6, k2d6-thinking, k2d6-agent, k2d6-agent-ultra, ok-computer"
        )
        return
    client = get_client(update.effective_user.id)
    client.model = model
    await update.message.reply_text(f"Model switched to: {model}")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <your question>")
        return
    client = get_client(update.effective_user.id)
    thinking = await update.message.reply_text("Searching...")
    reply = client.chat(query, use_search=True)
    await thinking.edit_text(reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    client = get_client(update.effective_user.id)
    thinking = await update.message.reply_text("Thinking...")
    reply = client.chat(user_text)
    await thinking.edit_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = get_client(update.effective_user.id)
    thinking = await update.message.reply_text("Uploading image...")

    photos = update.message.photo
    file = await context.bot.get_file(photos[-1].file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    buf.seek(0)

    file_id = client.upload_file(buf, "photo.jpg")

    caption = update.message.caption or "Describe this image"
    await thinking.edit_text("Analyzing...")
    reply = client.chat(caption, refs=[file_id])
    await thinking.edit_text(reply)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = get_client(update.effective_user.id)
    doc = update.message.document
    thinking = await update.message.reply_text(f"Uploading {doc.file_name}...")

    file = await context.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    buf.seek(0)

    file_id = client.upload_file(buf, doc.file_name)

    caption = update.message.caption or "Summarize this file"
    await thinking.edit_text("Analyzing...")
    reply = client.chat(caption, refs=[file_id])
    await thinking.edit_text(reply)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("new", new_chat))
app.add_handler(CommandHandler("model", switch_model))
app.add_handler(CommandHandler("search", search))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

print("Bot is running...")
app.run_polling()
```

---

## Run It

```bash
export TELEGRAM_TOKEN="your-telegram-bot-token"
export KIMI_TOKEN="your-kimi-bearer-token"

python bot.py
```

---

## Streaming Version

For a smoother experience, stream the reply and update the message progressively:

```python
async def handle_message_stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    client = get_client(update.effective_user.id)

    msg = await update.message.reply_text("...")
    full_reply = ""

    for chunk in client.stream(user_text):
        full_reply += chunk
        if len(full_reply) % 60 == 0:
            await msg.edit_text(full_reply)

    await msg.edit_text(full_reply)
```

Register it instead of `handle_message`:

```python
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_stream))
```

---

## Batch Image Upload Example

Send multiple images at once and ask Kimi to compare them:

```python
async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = get_client(update.effective_user.id)
    thinking = await update.message.reply_text("Uploading images...")

    file_ids = []
    for photo_list in [update.message.photo]:
        file = await context.bot.get_file(photo_list[-1].file_id)
        buf = io.BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)
        fid = client.upload_file(buf, "photo.jpg")
        file_ids.append(fid)

    await thinking.edit_text("Analyzing...")
    reply = client.chat("Compare these images", refs=file_ids)
    await thinking.edit_text(reply)
```

---

## Model Switching in Bot

```python
from kimi_nocost import Models

client = KimiClient(token=KIMI_TOKEN, model=Models.K2D6)

client.model = Models.K2D6_THINKING
reply = client.chat("Solve this math problem step by step: ...")
```

---

## REST API Usage

If you're running the included Flask server:

```bash
python examples/server.py
```

### Create a new session

```bash
curl -X POST http://localhost:8080/chat/new \
  -H "Authorization: Bearer YOUR_KIMI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bot-session"}'
```

### Send a message with a file

```bash
FILE_ID=$(curl -s -X POST http://localhost:8080/upload/file \
  -H "Authorization: Bearer YOUR_KIMI_TOKEN" \
  -F "file=@report.pdf" | python3 -c "import sys,json; print(json.load(sys.stdin)['file_id'])")

curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer YOUR_KIMI_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Summarize this\", \"file_ids\": [\"$FILE_ID\"]}"
```

### Upload images (up to 20)

```bash
curl -X POST http://localhost:8080/upload/images \
  -H "Authorization: Bearer YOUR_KIMI_TOKEN" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.png"
```

---

## Quick Test (No Telegram)

```python
from kimi_nocost import KimiClient, Models
import io

client = KimiClient(token="your-kimi-token")

print(client.chat("What is 2 + 2?"))
print(client.chat("Now multiply that by 10."))

content = b"Revenue Q1: $1M, Q2: $1.5M, Q3: $2M"
file_id = client.upload_file(io.BytesIO(content), "revenue.txt")
print(client.chat("Summarize this data", refs=[file_id]))

client.new_chat()
print(client.chat("What did we talk about?"))
```

---

## Community

<div align="center">

<a href="https://t.me/pythontodayz">
  <img src="https://img.shields.io/badge/Telegram-%40pythontodayz-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"/>
</a>

Follow for more Python projects → [t.me/pythontodayz](https://t.me/pythontodayz)

</div>
