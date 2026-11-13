from pathlib import Path
from fastapi.responses import FileResponse

import json
import urllib.request
import urllib.error

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.logger import logger


app = FastAPI(
    title="WordMate AI",
    version="0.1.0"
)


@app.get("/", include_in_schema=False)
def home():
    html_path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(html_path)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

class VocabularyRequest(BaseModel):
    word: str = Field(min_length=1, max_length=80)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "wordmate-ai"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    payload = {
        "model": "gemma3:1b",
        "messages": [
            {
                "role": "user",
                "content": request.message
            }
        ],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    ollama_request = urllib.request.Request(
        url="http://ollama:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            ollama_request,
            timeout=120
        ) as response:
            result = json.load(response)

    except TimeoutError:
        logger.exception("Ollama request timed out")
        raise HTTPException(
            status_code=504,
            detail="Ollama request timed out"
        )

    except urllib.error.URLError:
        logger.exception("Unable to connect to Ollama")
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Ollama"
        )

    try:
        return {
            "model": result["model"],
            "reply": result["message"]["content"]
        }

    except (KeyError, TypeError):
        logger.exception("Invalid Ollama response")
        raise HTTPException(
            status_code=502,
            detail="Invalid Ollama response"
        )


@app.post("/vocabulary/explain")
def explain_vocabulary(request: VocabularyRequest):

    word = request.word.strip()

    if not word:
        raise HTTPException(
            status_code=422,
            detail="Word cannot be empty"
        )

    prompt = f"""
You are a precise English dictionary assistant.

Target English word: {word}

Strict rules:
1. Write ALL explanations and translations in Traditional Chinese used in Taiwan.
2. Do NOT use Simplified Chinese.
3. Identify the correct parts of speech.
4. If the word has multiple parts of speech, explain each separately.
5. Provide the most common meaning first.
6. Give exactly two natural English example sentences.
7. Provide an accurate Traditional Chinese translation for each sentence.
8. Give two common collocations.
9. Keep the answer concise.
10. Do not ask follow-up questions.
11. If uncertain about a meaning, do not invent an explanation.

Use exactly this format:

單字：
詞性與中文意思：
例句 1：
中文翻譯 1：
例句 2：
中文翻譯 2：
常見搭配：
記憶技巧：
"""

    payload = {
        "model": "gemma3:1b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    ollama_request = urllib.request.Request(
        url="http://ollama:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            ollama_request,
            timeout=120
        ) as response:
            result = json.load(response)

    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Ollama request timed out"
        )

    except urllib.error.URLError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Ollama"
        )

    try:
        return {
            "word": word,
            "explanation": result["message"]["content"]
        }

    except (KeyError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Invalid Ollama response"
        )