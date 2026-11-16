"""WordMate AI FastAPI app — dictionary, saved vocabulary, and quizzes."""
import json
import random
import re
import sqlite3
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.database import clear_test_words, delete_word, get_word_by_id, get_words, init_db, save_word
from app.dictionary import DictionaryNotFound, DictionaryUnavailable, decode_saved, first_definition, lookup_word


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title='WordMate AI', version='1.0.0', lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class VocabularyRequest(BaseModel):
    word: str = Field(min_length=1, max_length=80)


class SaveWordRequest(BaseModel):
    word: str = Field(min_length=1, max_length=80)
    explanation: str = Field(min_length=1)


class QuizAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=80)


@app.get('/', include_in_schema=False)
def home():
    return FileResponse(Path(__file__).resolve().parent / 'static' / 'index.html')


@app.get('/health')
def health_check():
    return {'status': 'healthy', 'service': 'wordmate-ai'}


@app.post('/chat')
def chat(request: ChatRequest):
    """Optional Ollama chat retained for backwards compatibility; dictionary does not use it."""
    payload = {'model': 'gemma3:1b', 'messages': [{'role': 'user', 'content': request.message}], 'stream': False}
    req = urllib.request.Request('http://ollama:11434/api/chat',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.load(response)
        return {'model': data['model'], 'reply': data['message']['content']}
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, TypeError, ValueError) as e:
        raise HTTPException(502, 'Ollama unavailable or returned an invalid response') from e


@app.post('/vocabulary/explain')
def explain_vocabulary(request: VocabularyRequest):
    word = request.word.strip()
    if not word:
        raise HTTPException(422, 'Word cannot be empty')
    try:
        data = lookup_word(word)
    except DictionaryNotFound as e:
        raise HTTPException(404, str(e)) from e
    except DictionaryUnavailable as e:
        raise HTTPException(502, str(e)) from e
    return {'word': data['word'], 'dictionary': data,
            'explanation': json.dumps(data, ensure_ascii=False)}


@app.post('/vocabulary/save')
def save_vocabulary(request: SaveWordRequest):
    word = request.word.strip()
    if not word:
        raise HTTPException(422, 'Word cannot be empty')
    parsed = decode_saved(request.explanation)
    if not parsed or not first_definition(parsed):
        raise HTTPException(422, 'Expected structured dictionary explanation')
    if str(parsed.get('word', '')).strip().casefold() != word.casefold():
        raise HTTPException(422, 'Word does not match dictionary explanation')
    try:
        word_id = save_word(word, request.explanation)
    except sqlite3.IntegrityError as e:
        raise HTTPException(409, 'This word is already saved') from e
    return {'id': word_id, 'word': word, 'message': 'Word saved successfully'}


@app.get('/vocabulary/saved')
def saved_vocabulary():
    return {'words': [{**item, 'dictionary': decode_saved(item['explanation'])}
                      for item in get_words()]}


@app.delete('/vocabulary/{word_id}')
def delete_vocabulary(word_id: int):
    if not delete_word(word_id):
        raise HTTPException(404, 'Saved word not found')
    return {'id': word_id, 'message': 'Word deleted successfully'}


def extract_legacy_first_meaning(explanation: str) -> str | None:
    match = re.search(r'^\s*\d+\.\s*\[[^\]]+\]\s*[-–—]\s*(.+)$', explanation, re.MULTILINE)
    return match.group(1).strip() if match else None


@app.get('/quiz/question')
def get_quiz_question():
    candidates = []
    for item in get_words():
        meaning = first_definition(decode_saved(item['explanation']))
        if not meaning:
            meaning = extract_legacy_first_meaning(item['explanation'])
        if meaning:
            candidates.append({'id': item['id'], 'word': item['word'], 'meaning': meaning})
    if len(candidates) < 4:
        raise HTTPException(400, 'At least 4 valid saved words are required')
    selected = random.sample(candidates, 4)
    correct = random.choice(selected)
    options = [item['word'] for item in selected]
    random.shuffle(options)
    return {'question_id': correct['id'],
            'question': f'Which word means: {correct["meaning"]}?',
            'options': options}


@app.post('/quiz/answer')
def check_quiz_answer(request: QuizAnswerRequest):
    item = get_word_by_id(request.question_id)
    if item is None:
        raise HTTPException(404, 'Question not found')
    correct_answer = item['word']
    return {'correct': request.answer.strip().casefold() == correct_answer.strip().casefold(),
            'correct_answer': correct_answer}
