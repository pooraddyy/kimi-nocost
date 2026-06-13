from __future__ import annotations

import io
import json
import os
from typing import Generator, List, Union

import requests

from .errors import KimiAPIError, KimiAuthError, KimiSessionLimitError, KimiUploadError
from .models import Models
from .session import build_headers, create_chat, new_id, stream_completion, upload_file

MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_FILES = 1000
MAX_TOTAL_SIZE = 10 * 1024 * 1024 * 1024
MAX_IMAGES_PER_CALL = 20

FileInput = Union[str, os.PathLike, bytes, io.IOBase]


class KimiClient:
    def __init__(
        self,
        token: str,
        model: str,
        timeout: int = 60,
    ) -> None:
        if not token:
            raise KimiAuthError("token is required")
        if not model:
            raise KimiAuthError("model is required — e.g. model='kimi' or model='k2d6'")
        self.token = token
        self.model = model
        self.timeout = timeout
        self.device_id = new_id()
        self.session_id = new_id()
        self.chat_id: str = ""
        self.file_count: int = 0
        self.total_size: int = 0
        self.http = requests.Session()
        self.http.headers.update(build_headers(token, self.device_id, self.session_id))

    def new_chat(self, name: str = "") -> str:
        self.chat_id = create_chat(self.http, name, self.timeout)
        return self.chat_id

    def upload_single(self, file: FileInput, filename: str | None = None) -> str:
        if isinstance(file, (str, os.PathLike)):
            path = str(file)
            filename = filename or os.path.basename(path)
            size = os.path.getsize(path)
            if size > MAX_FILE_SIZE:
                raise KimiUploadError(f"{filename} exceeds 100 MB limit")
            if self.file_count >= MAX_FILES:
                raise KimiUploadError("max 1,000 files per user exceeded")
            if self.total_size + size > MAX_TOTAL_SIZE:
                raise KimiUploadError("total upload limit of 10 GB exceeded")
            with open(path, "rb") as fh:
                file_id = upload_file(self.http, fh, filename, self.timeout)
            self.file_count += 1
            self.total_size += size
            return file_id

        if isinstance(file, bytes):
            data = file
            file_obj = io.BytesIO(data)
        elif isinstance(file, io.IOBase):
            data = file.read()
            file_obj = io.BytesIO(data)
        else:
            raise KimiUploadError("file must be a path, bytes, or file-like object")

        if not filename:
            raise KimiUploadError("filename is required for bytes/stream uploads")
        size = len(data)
        if size > MAX_FILE_SIZE:
            raise KimiUploadError(f"{filename} exceeds 100 MB limit")
        if self.file_count >= MAX_FILES:
            raise KimiUploadError("max 1,000 files per user exceeded")
        if self.total_size + size > MAX_TOTAL_SIZE:
            raise KimiUploadError("total upload limit of 10 GB exceeded")
        file_id = upload_file(self.http, file_obj, filename, self.timeout)
        self.file_count += 1
        self.total_size += size
        return file_id

    def upload_images(
        self,
        files: List[Union[FileInput, tuple]],
    ) -> List[str]:
        if len(files) > MAX_IMAGES_PER_CALL:
            raise KimiUploadError(f"max {MAX_IMAGES_PER_CALL} images per call")
        ids = []
        for item in files:
            if isinstance(item, tuple):
                file_id = self.upload_single(item[0], item[1] if len(item) > 1 else None)
            else:
                file_id = self.upload_single(item)
            ids.append(file_id)
        return ids

    def upload_file(
        self,
        file: FileInput,
        filename: str | None = None,
    ) -> str:
        return self.upload_single(file, filename)

    def chat(
        self,
        message: str,
        chat_id: str = "",
        history: list | None = None,
        use_search: bool = False,
        refs: list | None = None,
    ) -> str:
        return "".join(
            self.stream(
                message,
                chat_id=chat_id,
                history=history,
                use_search=use_search,
                refs=refs,
            )
        )

    def stream(
        self,
        message: str,
        chat_id: str = "",
        history: list | None = None,
        use_search: bool = False,
        refs: list | None = None,
    ) -> Generator[str, None, None]:
        active_chat_id = chat_id or self.chat_id
        if not active_chat_id:
            active_chat_id = self.new_chat()
        else:
            self.chat_id = active_chat_id

        messages = list(history or []) + [{"role": "user", "content": message}]

        resp = stream_completion(
            self.http,
            active_chat_id,
            messages,
            self.model,
            use_search,
            self.timeout,
            refs=refs or [],
        )

        if not resp.ok:
            raise KimiAPIError(str(resp.status_code), resp.text[:300])

        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                continue
            event = obj.get("event", "")
            if event == "cmpl" and "text" in obj:
                yield obj["text"]
            elif event == "all_done":
                break
            elif "error_type" in obj or "error" in obj:
                code = obj.get("error_type") or str(obj.get("error", "unknown"))
                detail = obj.get("message", "")
                limit_keywords = (
                    "context_length", "token_limit", "too_long",
                    "context_limit", "length_exceed", "conversation_too_long",
                    "chat_context", "max_tokens",
                )
                if any(kw in code.lower() or kw in detail.lower() for kw in limit_keywords):
                    raise KimiSessionLimitError(code)
                raise KimiAPIError(code, detail)
