import json
from fastapi.testclient import TestClient
from app import main, database


def test_vocabulary_quiz_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'vocabulary.db')
    mock_data = lambda word: {'word': word, 'phonetic': '', 'source': 'test',
                              'meanings': [{'partOfSpeech': 'noun', 'definitions': [
                                  {'definition': f'The meaning of {word}', 'example': ''}]}]}
    monkeypatch.setattr(main, 'lookup_word', mock_data)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200
        for word in ('apple', 'audacity', 'implement', 'significant'):
            lookup = client.post('/vocabulary/explain', json={'word': word})
            assert lookup.status_code == 200, lookup.text
            body = lookup.json()
            assert body['dictionary']['meanings'][0]['partOfSpeech'] == 'noun'
            saved = client.post('/vocabulary/save', json={'word':word, 'explanation':body['explanation']})
            assert saved.status_code == 200, saved.text
        duplicated = client.post('/vocabulary/save', json={'word':'APPLE','explanation':json.dumps(mock_data('APPLE'))})
        assert duplicated.status_code == 409
        saved = client.get('/vocabulary/saved').json()['words']
        assert len(saved) == 4 and all(item['dictionary'] for item in saved)
        question = client.get('/quiz/question')
        assert question.status_code == 200, question.text
        data = question.json()
        assert len(data['options']) == 4
        word = next(item['word'] for item in saved if item['id'] == data['question_id'])
        assert client.post('/quiz/answer',json={'question_id':data['question_id'],'answer':word}).json()['correct']
        assert not client.post('/quiz/answer',json={'question_id':data['question_id'],'answer':'wrong'}).json()['correct']
        assert client.delete(f'/vocabulary/{saved[0]["id"]}').status_code == 200
        assert len(client.get('/vocabulary/saved').json()['words']) == 3
        assert client.get('/quiz/question').status_code == 400
        assert database.clear_test_words() == 3
        assert client.get('/vocabulary/saved').json()['words'] == []
