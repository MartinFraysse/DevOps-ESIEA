import fakeredis
import redis

import app as app_module
from app import alert_threshold, sanitize_input, app


class RedisEnPanne:
    """Faux client Redis qui ne repond jamais."""

    def ping(self):
        raise redis.ConnectionError("Redis injoignable")


def test_alert_threshold():
    assert alert_threshold() == 25


def test_sanitize_input_escapes_html():
    assert sanitize_input("<script>") == "&lt;script&gt;"


def test_health_endpoint(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis_client", lambda: fake)
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_endpoint_redis_down(monkeypatch):
    monkeypatch.setattr(app_module, "get_redis_client", lambda: RedisEnPanne())
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "error"


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/status")
    assert response.status_code == 200
    assert response.get_json()["service"] == "projet-devops-groupe-demo"


def test_visits_endpoint_increments_counter(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis_client", lambda: fake)
    client = app.test_client()
    assert client.get("/visits").get_json()["visits"] == 1
    assert client.get("/visits").get_json()["visits"] == 2
