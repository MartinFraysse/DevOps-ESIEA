import os

import redis
from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

app = Flask(__name__)

# Nombre de requetes recues, par methode, route et code de retour
REQUESTS = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP",
    ["method", "endpoint", "status"],
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


@app.after_request
def compter_requete(response):
    endpoint = nom_endpoint()
    # /metrics n'est pas compte, sinon chaque scrape de Prometheus fait monter le compteur
    if endpoint != "/metrics":
        REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    return response


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(debug=True)
