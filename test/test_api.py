
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "wordmate-ai"
    }


def test_health_not_rate_limited():
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200


def test_vocabulary_invalid_input():
    response = client.post(
        "/vocabulary/explain",
        json={"word": ""}
    )

    assert response.status_code == 422


def test_vocabulary_success():
    fake_response = {
        "message": {
            "content": "implement：實施、執行。"
        }
    }

    with patch(
        "app.main.urllib.request.urlopen"
    ) as mock_urlopen:

        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            b'{"message":{"content":"implement"}}'
        )

        response = client.post(
            "/vocabulary/explain",
            json={"word": "implement"}
        )

    assert response.status_code == 200
    assert response.json()["word"] == "implement"
    assert "explanation" in response.json()
