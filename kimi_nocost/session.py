import mimetypes
import time
import uuid

import requests
from requests.exceptions import ConnectionError as ConnError, Timeout

BASE = "https://kimi.moonshot.cn"
FILE_BASE = "https://www.kimi.com/apiv2-files"

RETRY_STATUS = {429, 500, 502, 503}
MAX_RETRIES = 3
BASE_DELAY = 1.0


def new_id():
    return uuid.uuid4().hex


def build_headers(token, device_id, session_id):
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        ),
        "Authorization": f"Bearer {token}",
        "Referer": "https://kimi.moonshot.cn/",
        "Origin": "https://kimi.moonshot.cn",
        "x-msh-device-id": device_id,
        "x-msh-session-id": session_id,
        "x-language": "en-US",
    }


def create_chat(http, name, timeout):
    name = name or f"chat-{uuid.uuid4().hex[:8]}"
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = http.post(
                f"{BASE}/api/chat",
                json={"name": name, "is_example": False},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["id"]
        except (ConnError, Timeout) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code not in RETRY_STATUS:
                raise
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
    raise last_exc


def upload_file(http, file_obj, filename, timeout):
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = http.post(
                f"{FILE_BASE}/file/upload",
                files={"file": (filename, file_obj, content_type)},
                headers={"Upload-Draft-Interop-Version": "6", "Upload-Complete": "?1"},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["file"]["id"]
        except (ConnError, Timeout) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code not in RETRY_STATUS:
                raise
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
    raise last_exc


def stream_completion(http, chat_id, messages, model, use_search, timeout, refs=None):
    body = {
        "messages": messages,
        "use_search": use_search,
        "extend": {"sidebar": True},
        "kimiplus_id": model,
        "use_research": False,
        "refs": refs or [],
        "refs_file": [],
    }
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = http.post(
                f"{BASE}/api/chat/{chat_id}/completion/stream",
                json=body,
                stream=True,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                timeout=timeout,
            )
            if r.status_code in RETRY_STATUS and attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
                continue
            return r
        except (ConnError, Timeout) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY * (2 ** attempt))
    if last_exc:
        raise last_exc
    return r
