import io
import os
from flask import Flask, Response, jsonify, request, stream_with_context
from kimi_nocost import KimiClient
from kimi_nocost.errors import KimiAPIError, KimiAuthError, KimiUploadError
from kimi_nocost.session import create_chat, build_headers, new_id
import requests as req_lib

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_IMAGES_PER_CALL = 20


def get_client():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    body = request.get_json(silent=True) or {}
    if not token:
        token = body.get("token", "")
    if not token:
        raise KimiAuthError("provide Authorization: Bearer <token>")
    model = body.get("model") or "kimi"
    return KimiClient(token=token, model=model)


def get_token():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token and request.is_json:
        token = (request.json or {}).get("token", "")
    if not token:
        raise KimiAuthError("provide Authorization: Bearer <token>")
    return token


@app.route("/chat/new", methods=["POST"])
def new_chat():
    try:
        token = get_token()
        body = request.get_json(force=True) or {}
        name = body.get("name", "")
        device_id = new_id()
        session_id = new_id()
        http = req_lib.Session()
        http.headers.update(build_headers(token, device_id, session_id))
        chat_id = create_chat(http, name, 60)
        return jsonify({"chat_id": chat_id})
    except KimiAuthError as e:
        return jsonify({"error": str(e)}), 401
    except KimiAPIError as e:
        return jsonify({"error": str(e), "code": e.code}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        client = get_client()
        body = request.get_json(force=True)
        message = body.get("message", "")
        if not message:
            return jsonify({"error": "message is required"}), 400
        chat_id = body.get("chat_id") or ""
        history = body.get("history") or []
        use_search = bool(body.get("use_search", False))
        model = body.get("model") or None
        refs = body.get("file_ids") or []
        if model:
            client.model = model
        reply = client.chat(message, chat_id=chat_id, history=history, use_search=use_search, refs=refs)
        return jsonify({"reply": reply, "chat_id": client.chat_id})
    except KimiAuthError as e:
        return jsonify({"error": str(e)}), 401
    except KimiAPIError as e:
        return jsonify({"error": str(e), "code": e.code}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    try:
        client = get_client()
        body = request.get_json(force=True)
        message = body.get("message", "")
        if not message:
            return jsonify({"error": "message is required"}), 400
        chat_id = body.get("chat_id") or ""
        history = body.get("history") or []
        use_search = bool(body.get("use_search", False))
        model = body.get("model") or None
        refs = body.get("file_ids") or []
        if model:
            client.model = model

        def generate():
            for chunk in client.stream(message, chat_id=chat_id, history=history, use_search=use_search, refs=refs):
                yield chunk

        return Response(stream_with_context(generate()), content_type="text/plain; charset=utf-8")
    except KimiAuthError as e:
        return jsonify({"error": str(e)}), 401
    except KimiAPIError as e:
        return jsonify({"error": str(e), "code": e.code}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload/images", methods=["POST"])
def upload_images():
    try:
        client = get_client()
        uploaded = request.files.getlist("images")
        if not uploaded:
            return jsonify({"error": "no images provided"}), 400
        if len(uploaded) > MAX_IMAGES_PER_CALL:
            return jsonify({"error": f"max {MAX_IMAGES_PER_CALL} images per call"}), 400
        file_ids = []
        for f in uploaded:
            data = f.read()
            if len(data) > MAX_FILE_SIZE:
                return jsonify({"error": f"{f.filename} exceeds 100 MB limit"}), 400
            file_id = client.upload_file(io.BytesIO(data), f.filename)
            file_ids.append(file_id)
        return jsonify({"file_ids": file_ids})
    except KimiUploadError as e:
        return jsonify({"error": str(e)}), 400
    except KimiAuthError as e:
        return jsonify({"error": str(e)}), 401
    except KimiAPIError as e:
        return jsonify({"error": str(e), "code": e.code}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload/file", methods=["POST"])
def upload_file_endpoint():
    try:
        client = get_client()
        f = request.files.get("file")
        if not f:
            return jsonify({"error": "no file provided"}), 400
        data = f.read()
        if len(data) > MAX_FILE_SIZE:
            return jsonify({"error": f"{f.filename} exceeds 100 MB limit"}), 400
        file_id = client.upload_file(io.BytesIO(data), f.filename)
        return jsonify({"file_id": file_id})
    except KimiUploadError as e:
        return jsonify({"error": str(e)}), 400
    except KimiAuthError as e:
        return jsonify({"error": str(e)}), 401
    except KimiAPIError as e:
        return jsonify({"error": str(e), "code": e.code}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
