import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Link, ClickEvent

client = TestClient(app)


@pytest.fixture
def existing_link():
    code = "test-" + uuid4().hex[:12]

    response = client.post(
        "/links",
        json={
            "long_url": "https://example.com/bootcamp",
            "tags": ["test"],
            "custom_code": code
        }
    )

    assert response.status_code == 200, response.text
    link_id = response.json()["id"]

    yield link_id, code

    db = SessionLocal()
    try:
        db.query(ClickEvent).filter(
            ClickEvent.link_id == link_id
        ).delete()
        db.query(Link).filter(Link.id == link_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def expired_link():
    code = "expired-" + uuid4().hex[:12]

    response = client.post(
        "/links",
        json={
            "long_url": "https://example.com/expired",
            "tags": ["test"],
            "custom_code": code,
            "expires_at": "2020-01-01T00:00:00Z"
        }
    )

    assert response.status_code == 200, response.text
    link_id = response.json()["id"]

    yield code

    db = SessionLocal()
    try:
        db.query(ClickEvent).filter(
            ClickEvent.link_id == link_id
        ).delete()
        db.query(Link).filter(Link.id == link_id).delete()
        db.commit()
    finally:
        db.close()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_list_links():
    response = client.get("/links")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_existing_link(existing_link):
    link_id, code = existing_link

    response = client.get(f"/links/{link_id}")

    assert response.status_code == 200
    assert response.json()["id"] == link_id
    assert response.json()["code"] == code


def test_get_nonexistent_link():
    response = client.get("/links/999999")
    assert response.status_code == 404


def test_redirect_existing_link(existing_link):
    link_id, code = existing_link

    response = client.get(
        f"/r/{code}",
        follow_redirects=False
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/bootcamp"


def test_redirect_invalid_code():
    response = client.get("/r/invalid123")
    assert response.status_code == 404


def test_redirect_expired_link(expired_link):
    response = client.get(f"/r/{expired_link}")
    assert response.status_code == 410


def test_negative_skip_validation():
    response = client.get("/links?skip=-1")
    assert response.status_code == 422


def test_excessive_limit_validation():
    response = client.get("/links?limit=101")
    assert response.status_code == 422


def test_reject_javascript_url():
    response = client.post(
        "/links",
        json={
            "long_url": "javascript:alert(1)",
            "tags": ["security-test"]
        }
    )

    assert response.status_code == 422
    assert "url_scheme" in response.text


def test_update_link(existing_link):
    link_id, code = existing_link

    response = client.put(
        f"/links/{link_id}",
        json={
            "long_url": "https://example.com/updated",
            "tags": ["updated", "test"]
        }
    )

    assert response.status_code == 200
    assert response.json()["long_url"] == "https://example.com/updated"


def test_update_nonexistent_link():
    response = client.put(
        "/links/999999",
        json={
            "long_url": "https://example.com/updated",
            "tags": []
        }
    )

    assert response.status_code == 404


def test_delete_link(existing_link):
    link_id, code = existing_link

    response = client.delete(f"/links/{link_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Link deleted successfully"

    check_response = client.get(f"/links/{link_id}")
    assert check_response.status_code == 404


def test_delete_nonexistent_link():
    response = client.delete("/links/999999")
    assert response.status_code == 404


def test_link_analytics(existing_link):
    link_id, code = existing_link

    response = client.get(f"/links/{link_id}/analytics")

    assert response.status_code == 200
    data = response.json()

    assert data["link_id"] == link_id
    assert data["short_code"] == code
    assert data["total_clicks"] == 0


def test_analytics_increases_after_redirect(existing_link):
    link_id, code = existing_link

    before = client.get(f"/links/{link_id}/analytics").json()
    assert before["total_clicks"] == 0

    redirect_response = client.get(
        f"/r/{code}",
        follow_redirects=False
    )
    assert redirect_response.status_code == 307

    after = client.get(f"/links/{link_id}/analytics")

    assert after.status_code == 200
    assert after.json()["total_clicks"] == 1


def test_analytics_nonexistent_link():
    response = client.get("/links/999999/analytics")
    assert response.status_code == 404
