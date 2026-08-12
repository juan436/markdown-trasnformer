import hmac
import logging
import os
import re
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from markitdown import MarkItDown
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("markdown-transformer")

API_KEY = os.environ["API_KEY"]
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE_MB", "20")) * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
SAFE_SUFFIX_RE = re.compile(r"^\.[A-Za-z0-9]{1,10}$")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

vision_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "PENDIENTE":
    vision_client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL)

app = FastAPI(title="markdown-transformer")
converter = MarkItDown()


def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _safe_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix
    return suffix if SAFE_SUFFIX_RE.match(suffix) else ""


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "vision_enabled": vision_client is not None}


@app.post("/convert", dependencies=[Depends(verify_api_key)])
async def convert(file: UploadFile = File(...)) -> dict:
    suffix = _safe_suffix(file.filename)
    size = 0

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        while chunk := await file.read(CHUNK_SIZE):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                tmp.close()
                os.unlink(tmp_path)
                raise HTTPException(status_code=413, detail="File too large")
            tmp.write(chunk)

    convert_kwargs = {}
    if vision_client is not None:
        convert_kwargs["llm_client"] = vision_client
        convert_kwargs["llm_model"] = GEMINI_MODEL

    try:
        result = converter.convert(tmp_path, **convert_kwargs)
    except Exception:
        logger.exception("Conversion failed for %s", file.filename)
        raise HTTPException(status_code=422, detail="File conversion failed") from None
    finally:
        os.unlink(tmp_path)

    return {"filename": file.filename, "markdown": result.text_content}
