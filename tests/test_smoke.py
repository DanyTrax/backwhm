from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_webhook_without_secret_accepts_empty_body():
    client = TestClient(app)
    r = client.post("/webhooks/pkgacct", json={"user": "test", "tarball": "/tmp/x.tar"})
    assert r.status_code == 200
