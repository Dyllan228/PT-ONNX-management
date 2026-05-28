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
