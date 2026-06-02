import io


def test_create_convert_task(client):
    pt_content = b"fake_pt_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("conv-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "conv-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.post("/api/convert", json={
        "model_id": model_id,
        "input_size": [640, 640],
        "dynamic_batch": True,
        "opset_version": 11,
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_convert_task(client):
    pt_content = b"fake_pt_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("conv-model2.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "conv-model2", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.get(f"/api/convert/{task_id}")
    assert response.status_code == 200
    assert "status" in response.json()


def test_convert_nonexistent_model(client):
    response = client.post("/api/convert", json={"model_id": 9999})
    assert response.status_code == 404


def test_get_task_status(client):
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("task-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "task-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "convert"
    assert data["status"] in ("pending", "running", "completed", "failed")


def test_delete_task(client):
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("del-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "del-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200

    get_resp = client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404
