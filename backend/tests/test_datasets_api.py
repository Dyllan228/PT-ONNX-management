def test_list_datasets(client):
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_dataset_bad_type(client):
    import io
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
