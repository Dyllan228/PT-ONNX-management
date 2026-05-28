import io
import time


def test_full_workflow_upload_convert(client):
    """Full workflow: upload model -> check in list -> create convert task -> check task."""
    # Upload
    pt_content = b"fake_integration_model"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("integration.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "integration-test", "version": "v1"},
    )
    assert upload_resp.status_code == 200
    model_id = upload_resp.json()["id"]

    # Check in list
    list_resp = client.get("/api/models")
    assert list_resp.status_code == 200
    model_ids = [m["id"] for m in list_resp.json()]
    assert model_id in model_ids

    # Get detail
    detail_resp = client.get(f"/api/models/{model_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "integration-test"

    # Create convert task (will fail due to fake model, but task should be created)
    convert_resp = client.post("/api/convert", json={"model_id": model_id})
    assert convert_resp.status_code == 200
    task_id = convert_resp.json()["task_id"]

    # Check task status
    time.sleep(2)  # Give the task some time to process
    task_resp = client.get(f"/api/tasks/{task_id}")
    assert task_resp.status_code == 200
    assert task_resp.json()["type"] == "convert"


def test_scan_endpoint(client):
    """POST /api/models/scan should trigger directory scan."""
    response = client.post("/api/models/scan")
    assert response.status_code == 200
    assert "scanned" in response.json()


def test_datasets_endpoint(client):
    """GET /api/datasets should return available datasets."""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_endpoint(client):
    """GET /api/health should return ok status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


def test_upload_then_delete_workflow(client):
    """Upload a model, verify it exists, delete it, verify it's gone."""
    pt_content = b"workflow_test_model"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("workflow-del.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "workflow-del", "version": "v1"},
    )
    assert upload_resp.status_code == 200
    model_id = upload_resp.json()["id"]

    # Verify exists
    get_resp = client.get(f"/api/models/{model_id}")
    assert get_resp.status_code == 200

    # Delete
    del_resp = client.delete(f"/api/models/{model_id}")
    assert del_resp.status_code == 200

    # Verify gone
    get_resp = client.get(f"/api/models/{model_id}")
    assert get_resp.status_code == 404
