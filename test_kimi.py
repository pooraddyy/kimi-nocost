import sys
import os
import io

sys.path.insert(0, os.path.dirname(__file__))

from kimi_nocost import KimiClient, Models
from kimi_nocost.errors import KimiAPIError, KimiUploadError

TOKEN = os.environ.get("KIMI_TOKEN", "")

def test_basic_chat():
    print("[1] Testing basic chat...")
    client = KimiClient(token=TOKEN, model="kimi")
    reply = client.chat("Say exactly: OK")
    assert reply.strip(), "Empty reply"
    print(f"    Reply: {reply.strip()[:80]}")
    print("    PASS")
    return client

def test_stream():
    print("[2] Testing streaming...")
    client = KimiClient(token=TOKEN, model="kimi")
    chunks = list(client.stream("Say exactly: STREAM_OK"))
    full = "".join(chunks)
    assert full.strip(), "Empty stream"
    print(f"    Chunks: {len(chunks)}, text: {full.strip()[:80]}")
    print("    PASS")

def test_models():
    print("[3] Testing Models class...")
    assert Models.KIMI == "kimi"
    assert Models.K1 == "k1"
    assert Models.K2D6 == "k2d6"
    assert Models.K2D6_AGENT == "k2d6-agent"
    print(f"    Models: {[v for k, v in vars(Models).items() if not k.startswith('__')]}")
    print("    PASS")

def test_model_switch():
    print("[4] Testing model switch via KimiClient...")
    client = KimiClient(token=TOKEN, model=Models.K2D6)
    assert client.model == "k2d6"
    client.model = Models.K1
    assert client.model == "k1"
    print(f"    model set to: {client.model}")
    print("    PASS")

def test_file_upload_and_refs():
    print("[5] Testing file upload + refs in completion...")
    client = KimiClient(token=TOKEN, model="kimi")
    content = b"The secret word is: BANANA42"
    file_id = client.upload_file(io.BytesIO(content), "test.txt")
    assert file_id, "No file ID returned"
    print(f"    file_id: {file_id}")
    reply = client.chat("What is the secret word in the file?", refs=[file_id])
    assert "BANANA42" in reply or "BANANA" in reply, f"Secret word not found in reply: {reply[:200]}"
    print(f"    Reply contains secret word: {reply.strip()[:120]}")
    print("    PASS")

def test_image_upload():
    print("[6] Testing image upload (batch)...")
    client = KimiClient(token=TOKEN, model="kimi")
    png_1x1 = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    ids = client.upload_images([
        (io.BytesIO(png_1x1), "img1.png"),
        (io.BytesIO(png_1x1), "img2.png"),
    ])
    assert len(ids) == 2, f"Expected 2 IDs, got {len(ids)}"
    print(f"    file_ids: {ids}")
    print("    PASS")

def test_no_underscore_attributes():
    print("[7] Testing no _ prefix on public attrs...")
    client = KimiClient(token=TOKEN, model="kimi")
    assert hasattr(client, "file_count"), "file_count missing"
    assert hasattr(client, "total_size"), "total_size missing"
    assert hasattr(client, "upload_single"), "upload_single missing"
    assert not hasattr(client, "_file_count"), "_file_count should not exist"
    assert not hasattr(client, "_total_size"), "_total_size should not exist"
    assert not hasattr(client, "_upload_single"), "_upload_single should not exist"
    print("    PASS")

def test_limit_images():
    print("[8] Testing image upload limit (>20 should raise)...")
    client = KimiClient(token=TOKEN, model="kimi")
    png_1x1 = b'\x89PNG\r\n\x1a\n'
    try:
        client.upload_images([(io.BytesIO(png_1x1), f"img{i}.png") for i in range(21)])
        print("    FAIL (should have raised)")
        sys.exit(1)
    except KimiUploadError as e:
        print(f"    Correctly raised KimiUploadError: {e}")
        print("    PASS")

def test_file_size_limit():
    print("[9] Testing file size limit (>100MB should raise)...")
    client = KimiClient(token=TOKEN, model="kimi")
    try:
        client.upload_file(io.BytesIO(b"x" * (101 * 1024 * 1024)), "big.bin")
        print("    FAIL (should have raised)")
        sys.exit(1)
    except KimiUploadError as e:
        print(f"    Correctly raised KimiUploadError: {e}")
        print("    PASS")

def test_missing_model_error():
    print("[10] Testing error when model not provided...")
    try:
        KimiClient(token=TOKEN)
        print("    FAIL (should have raised TypeError)")
        sys.exit(1)
    except TypeError as e:
        print(f"    Correctly raised TypeError: {e}")
        print("    PASS")

def test_plain_string_model():
    print("[11] Testing plain string model...")
    client = KimiClient(token=TOKEN, model="k2d6")
    assert client.model == "k2d6"
    client.model = "k1"
    assert client.model == "k1"
    print(f"    model='k2d6' set, switched to 'k1'")
    print("    PASS")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: KIMI_TOKEN not set")
        sys.exit(1)

    print(f"Token loaded ({len(TOKEN)} chars)\n")

    try:
        test_basic_chat()
        test_stream()
        test_models()
        test_model_switch()
        test_file_upload_and_refs()
        test_image_upload()
        test_no_underscore_attributes()
        test_limit_images()
        test_file_size_limit()
        test_missing_model_error()
        test_plain_string_model()
        print("\nAll tests PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
