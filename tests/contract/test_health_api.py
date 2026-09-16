from uuid import uuid4


def test_health_returns_stable_api_shape_and_request_id(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["request_id"] == response.headers["X-Request-ID"]


def test_valid_incoming_request_id_is_preserved(client):
    request_id = str(uuid4())

    response = client.get("/api/v1/health", headers={"X-Request-ID": request_id})

    assert response.json["request_id"] == request_id


def test_invalid_incoming_request_id_is_replaced(client):
    response = client.get("/api/v1/health", headers={"X-Request-ID": "not-a-uuid"})

    assert response.json["request_id"] != "not-a-uuid"
