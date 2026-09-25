import fakeredis
import redis
from prometheus_client import REGISTRY

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
    assert "deploy_color" in response.get_json()
    assert "commit" in response.get_json()


def test_visits_endpoint_increments_counter(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis_client", lambda: fake)
    client = app.test_client()
    assert client.get("/visits").get_json()["visits"] == 1
    assert client.get("/visits").get_json()["visits"] == 2


def nb_requetes(method, endpoint, status):
    """Valeur actuelle du compteur http_requests_total (0 si la serie n'existe pas encore)."""
    labels = {"method": method, "endpoint": endpoint, "status": status}
    return REGISTRY.get_sample_value("http_requests_total", labels) or 0


def test_compteur_augmente_a_chaque_requete():
    client = app.test_client()
    avant = nb_requetes("GET", "/status", "200")
    client.get("/status")
    client.get("/status")
    assert nb_requetes("GET", "/status", "200") == avant + 2


def test_url_inconnue_regroupee():
    client = app.test_client()
    avant = nb_requetes("GET", "unknown", "404")
    client.get("/nimportequoi")
    assert nb_requetes("GET", "unknown", "404") == avant + 1


def test_metrics_ne_se_compte_pas():
    client = app.test_client()
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.get_data(as_text=True)
    client.get("/metrics")
    assert nb_requetes("GET", "/metrics", "200") == 0
