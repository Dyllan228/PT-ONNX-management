import io


def test_create_benchmark_nonexistent_model(client):
    response = client.post("/api/benchmark", json={
        "model_ids": [9999],
        "model_types": ["pt"],
        "devices": ["cpu"],
    })
    assert response.status_code == 404


def test_get_benchmark_task_not_found(client):
    response = client.get("/api/benchmark/nonexistent")
    assert response.status_code == 404


def test_create_benchmark_task(client):
    """Upload a model then create a benchmark task."""
    pt_content = b"fake_benchmark_model"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("bench-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "bench-model", "version": "v1"},
    )
    assert upload_resp.status_code == 200
    model_id = upload_resp.json()["id"]

    resp = client.post("/api/benchmark", json={
        "model_ids": [model_id],
        "model_types": ["pt"],
        "devices": ["cpu"],
        "num_runs": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_benchmark_task_status(client):
    """Create a benchmark task then query its status."""
    pt_content = b"fake_bench_status_model"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("bench-status.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "bench-status", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    task_resp = client.post("/api/benchmark", json={
        "model_ids": [model_id],
        "model_types": ["pt"],
        "devices": ["cpu"],
    })
    task_id = task_resp.json()["task_id"]

    resp = client.get(f"/api/benchmark/{task_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("pending", "running", "completed", "failed")
