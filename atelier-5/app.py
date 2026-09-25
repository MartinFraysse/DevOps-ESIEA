import os
import time

import redis
from flask import Flask, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

# Nombre de requetes recues, par methode, route et code de retour
REQUESTS = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP",
    ["method", "endpoint", "status"],
)

# Temps de traitement des requetes, en secondes (histogramme : on peut calculer un p95 ensuite)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duree de traitement des requetes HTTP",
    ["method", "endpoint"],
    # Seaux plus petits que ceux par defaut (5 ms minimum) : nos requetes prennent moins de 5 ms,
    # avec les seaux par defaut tout tombait dans le premier et le p95 ne voulait rien dire
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)

ALERT_THRESHOLD = 25


def alert_threshold():
    """Seuil d'alerte au-dessus duquel une notification est declenchee."""
    return ALERT_THRESHOLD


def sanitize_input(value):
    """Echappe les caracteres dangereux d'une entree utilisateur."""
    return value.replace("<", "&lt;").replace(">", "&gt;")


@app.route("/health")
def health():
    """Verifie que Redis repond, sinon renvoie 503."""
    try:
        get_redis_client().ping()
    except redis.RedisError:
        return jsonify(status="error", redis="down"), 503
    return jsonify(status="ok", redis="ok"), 200


@app.route("/status")
def status():
    return jsonify(
        service="projet-devops-groupe-demo",
        version="1.0",
        # Couleur du conteneur (blue ou green), donnee par docker-compose
        deploy_color=os.environ.get("DEPLOY_COLOR", "unknown"),
        # SHA du commit, mis dans l'image au moment du build par la CI
        commit=os.environ.get("GIT_SHA", "unknown"),
    ), 200


def get_redis_client():
    """Cree un client Redis a partir de la configuration de l'environnement."""
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        decode_responses=True,
        # Sans timeout, /health reste bloque si Redis ne repond pas
        socket_connect_timeout=2,
        socket_timeout=2,
    )


@app.route("/visits")
def visits():
    count = get_redis_client().incr("visits")
    return jsonify(visits=count), 200


def nom_endpoint():
    """Route Flask de la requete (ex : /visits), ou 'unknown' si aucune route ne correspond."""
    # On prend la route et pas l'URL brute :
    # sinon chaque URL inventee (/azerty...) cree une serie de plus
    if request.url_rule is None:
        return "unknown"
    return request.url_rule.rule


@app.route("/simulate-error")
def simulate_error():
    """Renvoie toujours une erreur 500, pour tester l'alerte."""
    return jsonify(status="error", message="erreur simulee"), 500


@app.before_request
def demarrer_chrono():
    g.debut = time.perf_counter()


@app.after_request
def enregistrer_metriques(response):
    endpoint = nom_endpoint()
    # /metrics n'est pas compte, sinon chaque scrape de Prometheus fait monter les metriques
    if endpoint != "/metrics":
        REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
        LATENCY.labels(request.method, endpoint).observe(time.perf_counter() - g.debut)
    return response


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(debug=True)
