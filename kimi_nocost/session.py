import mimetypes
import uuid
import requests

BASE = "https://kimi.moonshot.cn"
FILE_BASE = "https://www.kimi.com/apiv2-files"


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
    r = http.post(
        f"{BASE}/api/chat",
        json={"name": name, "is_example": False},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["id"]


def upload_file(http, file_obj, filename, timeout):
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    r = http.post(
        f"{FILE_BASE}/file/upload",
        files={"file": (filename, file_obj, content_type)},
        headers={"Upload-Draft-Interop-Version": "6", "Upload-Complete": "?1"},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["file"]["id"]


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
    return http.post(
        f"{BASE}/api/chat/{chat_id}/completion/stream",
        json=body,
        stream=True,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        timeout=timeout,
    )
