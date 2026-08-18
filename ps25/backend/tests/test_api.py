import os
from unittest.mock import patch

# Set COE_API_KEY for unit test environment before importing app
os.environ.setdefault("COE_API_KEY", "test-coe-api-key")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_empty_query():
    # Test empty query string
    response = client.post("/ask", json={"query": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Query cannot be empty or whitespace-only."}


def test_ask_whitespace_query():
    # Test whitespace-only query
    response = client.post("/ask", json={"query": "   \n\t  "})
    assert response.status_code == 400
    assert response.json() == {"detail": "Query cannot be empty or whitespace-only."}


@patch("backend.main.answer_query")
def test_ask_success(mock_answer_query):
    mock_answer_query.return_value = {
        "answer": "According to the Code on Wages, 2019...",
        "sources": ["Code on Wages, 2019, Section 17"]
    }

    query_text = "My employer has not paid my salary for three months."
    response = client.post("/ask", json={"query": query_text})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "According to the Code on Wages, 2019...",
        "sources": ["Code on Wages, 2019, Section 17"]
    }
    mock_answer_query.assert_called_once_with(query_text)


@patch("backend.main.answer_query")
def test_ask_rag_exception(mock_answer_query):
    mock_answer_query.side_effect = RuntimeError("OpenAI API Connection Error / Secret Key Invalid")

    response = client.post("/ask", json={"query": "My boss isn't paying me."})

    assert response.status_code == 500
    # Confirm response is sanitized and contains no stack traces, paths, or secrets
    assert response.json() == {"detail": "AI service temporarily unavailable."}
