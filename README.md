<div align="center">

<h1>kimi-nocost</h1>

<p>Unofficial Python client for <strong>Kimi AI</strong> (kimi.moonshot.cn). No API key needed — just your bearer token.</p>

<a href="https://pypi.org/project/kimi-nocost/"><img src="https://img.shields.io/pypi/v/kimi-nocost?color=6c5ce7&label=PyPI&logo=pypi&logoColor=white&style=for-the-badge" alt="PyPI Version"/></a>
<a href="https://pypi.org/project/kimi-nocost/"><img src="https://img.shields.io/pypi/pyversions/kimi-nocost?color=00b894&logo=python&logoColor=white&style=for-the-badge" alt="Python Versions"/></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-fdcb6e?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/></a>
<a href="https://t.me/pythontodayz"><img src="https://img.shields.io/badge/Telegram-Join%20Channel-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"/></a>

</div>

---

## Features

- No API key required — uses your browser session token
- Persistent sessions — messages stay in the same conversation automatically
- Streaming support — yield reply chunks in real time
- Web search — toggle Kimi's built-in search on any message
- Multi-turn conversations — full context preserved across calls
- Image upload — send up to 20 images at once
- File upload — send documents, PDFs, code files (max 100 MB each, 1,000 files, 10 GB total)
- Built-in Models — switch models easily with `Models.K2D6`, `Models.K2D6_AGENT`, etc.
- Lightweight — only depends on `requests`

---

## Install

```bash
pip install kimi-nocost
```

---

## Quick Start

```python
from kimi_nocost import KimiClient

client = KimiClient(token="your-kimi-bearer-token", model="kimi")

reply = client.chat("What is the capital of France?")
print(reply)
```

> `model` is required. Pass it as a plain string — `"kimi"`, `"k1"`, `"k2d6"`, etc.
> Omitting it raises a `TypeError`.

---

## Models

Use the built-in `Models` class to switch between Kimi models:

```python
from kimi_nocost import KimiClient, Models

client = KimiClient(token="your-token", model=Models.KIMI)

reply = client.chat("Explain transformers")
print(reply)

client.model = Models.K2D6
reply = client.chat("Solve this step by step: 2x + 5 = 13")
print(reply)
```

| Constant | Model ID | Description |
|----------|----------|-------------|
| `Models.KIMI` | `kimi` | Default model |
| `Models.K1` | `k1` | K1 model |
| `Models.K2D6` | `k2d6` | K2.6 Instant — fast responses |
| `Models.K2D6_AGENT` | `k2d6-agent` | K2.6 Agent — research, slides, docs |

---

## Multi-Turn Conversation

```python
client = KimiClient(token="your-token", model="kimi")

reply1 = client.chat("My name is Alex.")
reply2 = client.chat("What is my name?")
print(reply2)
```

---

## Streaming

```python
from kimi_nocost import KimiClient

client = KimiClient(token="your-token", model="kimi")

for chunk in client.stream("Explain quantum computing in simple terms"):
    print(chunk, end="", flush=True)
```

---

## With Web Search

```python
reply = client.chat("Latest news on AI today", use_search=True)
```

---

## Image Upload

Send up to 20 images in a single call:

```python
from kimi_nocost import KimiClient

client = KimiClient(token="your-token", model="kimi")

file_ids = client.upload_images([
    "photo1.jpg",
    "photo2.png",
    (open("screenshot.png", "rb"), "screenshot.png"),
])

reply = client.chat("Describe these images", refs=file_ids)
print(reply)
```

---

## File Upload

Send documents, PDFs, or code files (max 100 MB each, 1,000 files per session, 10 GB total):

```python
file_id = client.upload_file("report.pdf")

reply = client.chat("Summarize this document", refs=[file_id])
print(reply)
```

You can also pass raw bytes with a filename:

```python
import io

content = b"def hello(): print('world')"
file_id = client.upload_file(io.BytesIO(content), "hello.py")

reply = client.chat("What does this code do?", refs=[file_id])
print(reply)
```

---

## Starting a New Chat

```python
client.new_chat(name="fresh-start")
reply = client.chat("Let's start over.")
```

---

## Manual Chat ID

```python
chat_id = client.new_chat(name="my-session")

reply1 = client.chat("My name is Alex.", chat_id=chat_id)
reply2 = client.chat("What is my name?", chat_id=chat_id)
print(reply2)
```

---

## API Reference

### `KimiClient(token, model, timeout=60)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | `str` | Bearer JWT from kimi.moonshot.cn |
| `model` | `str` | Model ID — use `Models.*` constants |
| `timeout` | `int` | HTTP timeout in seconds |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `chat(message, chat_id, history, use_search, refs)` | `str` | Send a message, get full reply |
| `stream(message, chat_id, history, use_search, refs)` | `Generator[str]` | Send a message, yield reply chunks |
| `new_chat(name)` | `str` | Create a new conversation and set it as active |
| `upload_file(file, filename)` | `str` | Upload a file, returns file ID |
| `upload_images(files)` | `List[str]` | Upload up to 20 images, returns list of file IDs |
| `upload_single(file, filename)` | `str` | Upload a single file or image, returns file ID |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `str` | Current model — change anytime |
| `chat_id` | `str` | Active conversation ID |
| `file_count` | `int` | Number of files uploaded this session |
| `total_size` | `int` | Total bytes uploaded this session |

---

## REST API Server

The included Flask server exposes HTTP endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /chat/new` | POST | Create a new session → returns `chat_id` |
| `POST /chat` | POST | Send a message → returns `reply` + `chat_id` |
| `POST /chat/stream` | POST | Stream a reply as plain text |
| `POST /upload/images` | POST | Upload up to 20 images → returns `file_ids` |
| `POST /upload/file` | POST | Upload a single file → returns `file_id` |
| `GET /health` | GET | Health check |

Pass your token via `Authorization: Bearer <token>` header.

**Chat with files:**
```json
{
  "message": "Summarize this",
  "file_ids": ["id1", "id2"],
  "model": "k2d6-agent"
}
```

**Upload images** (multipart, field name `images`):
```bash
curl -H "Authorization: Bearer <token>" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.png" \
  http://localhost:8080/upload/images
```

**Upload file** (multipart, field name `file`):
```bash
curl -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  http://localhost:8080/upload/file
```

---

## Getting Your Token

1. Open [kimi.moonshot.cn](https://kimi.moonshot.cn) in your browser
2. Open **DevTools** → **Network** → any request
3. Copy the value of `Authorization: Bearer <token>`

Or from iOS/Android using a MITM proxy (e.g. mitmproxy, Charles).

The token is a JWT that lasts ~30 days.

---

## Demo

See [DEMO.md](DEMO.md) for a full working Telegram bot with image & file upload support.

---

## Community

<div align="center">

<a href="https://t.me/pythontodayz">
  <img src="https://img.shields.io/badge/Telegram-%40pythontodayz-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Channel"/>
</a>

Join for Python tutorials, projects, and updates → [t.me/pythontodayz](https://t.me/pythontodayz)

</div>

---

## License

MIT — made by [addy](https://t.me/pythontodayz)
