import os

import redis
from flask import Flask, jsonify

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True)
