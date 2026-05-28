import io


def test_create_inference_task_no_file(client):
    """Inference without any data source should return 400."""
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("inf-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "inf-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.post("/api/inference", data={
        "model_id": model_id,
        "model_type": "pt",
        "device": "cpu",
    })
    assert response.status_code == 400


def test_create_inference_task_nonexistent_model(client):
    """Inference with nonexistent model should return 404."""
    response = client.post("/api/inference", data={
        "model_id": 9999,
        "model_type": "pt",
        "device": "cpu",
    })
    assert response.status_code == 404


def test_create_inference_task_unsupported_file(client):
    """Inference with unsupported file type should return 400."""
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("inf-model2.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "inf-model2", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.post(
        "/api/inference",
        data={"model_id": model_id, "model_type": "pt", "device": "cpu"},
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


def test_get_inference_task_not_found(client):
    response = client.get("/api/inference/nonexistent")
    assert response.status_code == 404
