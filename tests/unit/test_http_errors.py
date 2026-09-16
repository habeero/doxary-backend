def test_unknown_route_is_not_internal_error(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json["error"]["code"] == "not_found"
    assert "Traceback" not in response.get_data(as_text=True)


def test_unsupported_method_is_405(client):
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json["error"]["code"] == "method_not_allowed"
