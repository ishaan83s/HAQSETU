import os
from unittest.mock import patch

# Set COE_API_KEY for unit test environment before importing app
os.environ.setdefault("COE_API_KEY", "test-coe-api-key")

from fastapi.testclient import TestClient
from backend.main import app, incidents_store

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


def test_auth_request_otp():
    # Valid phone
    response = client.post("/auth/request-otp", json={"phoneNumber": "+919876543210"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["otpSent"] is True

    # Invalid phone
    response = client.post("/auth/request-otp", json={"phoneNumber": "123"})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_PHONE"


def test_auth_verify_otp():
    # Valid OTP
    response = client.post("/auth/verify-otp", json={"phoneNumber": "+919876543210", "otp": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert "userId" in data["data"]

    # Invalid OTP format
    response = client.post("/auth/verify-otp", json={"phoneNumber": "+919876543210", "otp": "abc"})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_OTP"


def test_user_context():
    response = client.put("/users/context", json={
        "state": "Maharashtra",
        "roleCategory": "worker",
        "vulnerabilityTags": ["gig_worker"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["saved"] is True


@patch("backend.main.answer_query")
def test_create_incident_text_success(mock_answer_query):
    mock_answer_query.return_value = {
        "answer": "Under the Code on Wages, 2019, Section 17, wages must be paid promptly.",
        "sources": ["Code on Wages, 2019, Section 17"]
    }

    query_text = "My boss keeps delaying my money even though I already did the work."
    response = client.post("/incidents", json={
        "inputMode": "text",
        "language": "en",
        "text": query_text,
        "audioBase64": None
    })

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    incident_data = body["data"]
    assert incident_data["incidentId"] is not None
    assert incident_data["triage"]["cards"]["whatMayBeHappening"]["text"] == "Under the Code on Wages, 2019, Section 17, wages must be paid promptly."
    assert len(incident_data["triage"]["cards"]["whatMayProtectYou"]) == 1
    assert incident_data["triage"]["cards"]["whatMayProtectYou"][0]["source"]["title"] == "Code on Wages, 2019, Section 17"
    mock_answer_query.assert_called_once_with(query_text)

    # Verify retrieval via GET /incidents/{incidentId}
    incident_id = incident_data["incidentId"]
    get_res = client.get(f"/incidents/{incident_id}")
    assert get_res.status_code == 200
    get_body = get_res.json()
    assert get_body["success"] is True
    assert get_body["data"]["incidentId"] == incident_id


def test_create_incident_empty_text():
    response = client.post("/incidents", json={
        "inputMode": "text",
        "language": "en",
        "text": "   ",
        "audioBase64": None
    })
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMPTY_TEXT"


def test_create_incident_voice():
    response = client.post("/incidents", json={
        "inputMode": "voice",
        "language": "en",
        "text": None,
        "audioBase64": "dummy-base64-audio"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["emptyTranscription"] is True


def test_get_incident_not_found():
    response = client.get("/incidents/non_existent_id")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"


@patch("backend.main.answer_query")
def test_create_incident_exception_handling(mock_answer_query):
    mock_answer_query.side_effect = RuntimeError("OpenAI connection timed out")

    response = client.post("/incidents", json={
        "inputMode": "text",
        "language": "en",
        "text": "Help with wages",
        "audioBase64": None
    })
    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AI_SERVICE_ERROR"
    # Ensure error message is safe
    assert "OpenAI" not in body["error"]["message"]
