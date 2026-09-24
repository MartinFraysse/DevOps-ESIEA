#!/usr/bin/env bash
# Déploiement blue/green avec rollback automatique.
#
# Usage : ./deploy/deploy.sh <tag de l'image>
#   ex :  ./deploy/deploy.sh local
#
# 1. regarde quelle couleur est active (fichier deploy/.active-color)
# 2. lance la nouvelle version sur l'autre couleur
# 3. attend qu'elle réponde sur /health, puis vérifie /status (smoke test)
# 4. si tout est bon : nginx passe sur la nouvelle couleur, puis on arrête l'ancienne
#    sinon : on arrête la nouvelle et l'ancienne couleur reste active

set -euo pipefail

# On se place dans atelier-4/, là où est le docker-compose.yml
cd "$(dirname "$0")/.."

TAG="${1:?Usage : ./deploy/deploy.sh <tag de l image>}"
export IMAGE_TAG="$TAG"

STATE_FILE=deploy/.active-color
NGINX_CONF=deploy/nginx/active.conf
TEMPLATE=deploy/nginx/app.conf.template

# --- 1. Couleur active et nouvelle couleur ---
ACTIVE=$(cat "$STATE_FILE" 2>/dev/null || echo "none")
if [ "$ACTIVE" = "blue" ]; then
    NEW=green
else
    NEW=blue
fi
echo "Couleur active : $ACTIVE -> déploiement de l'image '$TAG' sur : $NEW"

# Premier déploiement (ou machine neuve en CI) : on démarre redis et nginx.
# Il n'y a encore aucune version en production, donc on peut déjà faire pointer nginx sur la nouvelle couleur.
if [ "$ACTIVE" = "none" ]; then
    sed "s/COLOR/$NEW/" "$TEMPLATE" > "$NGINX_CONF"
    docker compose up -d --wait redis nginx
fi

# --- 2. Lancer la nouvelle version ---
# --no-deps : ne pas relancer redis s'il est arrêté (sinon on ne peut pas tester l'échec)
docker compose --profile "$NEW" up -d --no-deps "app-$NEW"

# Appelle l'app depuis le conteneur nginx (les apps n'ont pas de port ouvert sur la machine)
appel() {
    docker compose exec -T nginx wget -qO- "http://app-$NEW:5000/$1"
}

echec() {
    echo "ÉCHEC : $1"
    echo "On arrête $NEW, la couleur active reste : $ACTIVE"
    docker compose --profile "$NEW" stop "app-$NEW"
    exit 1
}

# --- 3. Attendre /health (10 essais, 3 secondes entre chaque) ---
OK=false
for i in $(seq 1 10); do
    if appel health > /dev/null 2>&1; then
        OK=true
        break
    fi
    echo "  /health pas encore OK (essai $i/10)"
    sleep 3
done
if [ "$OK" = false ]; then
    echec "/health ne répond pas 200"
fi
echo "/health OK"

# Smoke test : /status doit répondre avec la bonne couleur
STATUS=$(appel status 2> /dev/null || true)
COULEUR=$(echo "$STATUS" | jq -r '.deploy_color' 2> /dev/null || true)
if [ "$COULEUR" != "$NEW" ]; then
    echec "/status renvoie la couleur '$COULEUR' au lieu de '$NEW'"
fi
echo "Smoke test OK : $STATUS"

# --- 4. Bascule, dans cet ordre : nginx d'abord, puis on arrête l'ancienne couleur ---
sed "s/COLOR/$NEW/" "$TEMPLATE" > "$NGINX_CONF"
docker compose exec -T nginx nginx -s reload
echo "$NEW" > "$STATE_FILE"

if [ "$ACTIVE" != "none" ]; then
    docker compose --profile "$ACTIVE" stop "app-$ACTIVE"
fi

echo "Déploiement OK : $NEW est maintenant la couleur active"
