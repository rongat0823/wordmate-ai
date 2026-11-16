"""Dictionary API integration, with structured and sanitized outputs."""
import json
import urllib.error
import urllib.parse
import urllib.request

DICTIONARY_BASE = 'https://api.dictionaryapi.dev/api/v2/entries/en/'


class DictionaryNotFound(Exception):
    pass


class DictionaryUnavailable(Exception):
    pass


def parse_dictionary(entries: list, query: str) -> dict:
    """Normalize external dictionary response without guessing missing definitions."""
    if not isinstance(entries, list) or not entries:
        raise DictionaryUnavailable('Unexpected dictionary response')
    groups = []
    phonetic = ''
    word = query.strip()
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        word = str(entry.get('word') or word)
        phonetic = phonetic or str(entry.get('phonetic') or '')
        for item in entry.get('meanings') or []:
            if not isinstance(item, dict):
                continue
            part = str(item.get('partOfSpeech') or '').strip()
            definitions = []
            for d in item.get('definitions') or []:
                if not isinstance(d, dict):
                    continue
                meaning = str(d.get('definition') or '').strip()
                if not meaning:
                    continue
                key = (part.casefold(), meaning.casefold())
                if key in seen:
                    continue
                seen.add(key)
                definitions.append({
                    'definition': meaning,
                    'example': str(d.get('example') or '').strip()
                })
            if definitions:
                groups.append({'partOfSpeech': part or 'unknown', 'definitions': definitions})
    if not groups:
        raise DictionaryNotFound('No definitions available')
    return {'word': word, 'phonetic': phonetic, 'meanings': groups, 'source': 'Free Dictionary API'}


def lookup_word(word: str) -> dict:
    word = word.strip()
    if not word or len(word) > 80 or '/' in word or '\\' in word:
        raise DictionaryNotFound('Invalid word')
    url = DICTIONARY_BASE + urllib.parse.quote(word, safe='')
    req = urllib.request.Request(url, headers={'User-Agent': 'WordMateAI/1.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            entries = json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise DictionaryNotFound('Word not found') from e
        raise DictionaryUnavailable('Dictionary service error') from e
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise DictionaryUnavailable('Dictionary service unavailable') from e
    return parse_dictionary(entries, word)


def decode_saved(explanation: str) -> dict | None:
    try:
        data = json.loads(explanation)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get('meanings'), list):
        return None
    return data


def first_definition(data: dict | None) -> str | None:
    if not data:
        return None
    for meaning in data.get('meanings', []):
        for definition in meaning.get('definitions', []):
            value = str(definition.get('definition', '')).strip()
            if value:
                return value
    return None
