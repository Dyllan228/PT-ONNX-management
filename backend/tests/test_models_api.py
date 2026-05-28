import io


def test_list_models_empty(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_model(client):
    pt_content = b"fake_pt_model_content"
    response = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-model"
    assert data["version"] == "v1"
    assert data["onnx_converted"] is False


def test_get_model(client):
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.get(f"/api/models/{model_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test-model"


def test_get_model_not_found(client):
    response = client.get("/api/models/999")
    assert response.status_code == 404


def test_update_model(client):
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.put(
        f"/api/models/{model_id}",
        json={"name": "updated-model", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated-model"
    assert response.json()["description"] == "Updated description"


def test_delete_model(client):
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.delete(f"/api/models/{model_id}")
    assert response.status_code == 200

    get_resp = client.get(f"/api/models/{model_id}")
    assert get_resp.status_code == 404


def test_upload_bad_extension(client):
    response = client.post(
        "/api/models/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"name": "bad", "version": "v1"},
    )
    assert response.status_code == 400
