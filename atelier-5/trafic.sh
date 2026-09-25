#!/usr/bin/env bash
# Envoie du trafic à l'app pour voir bouger Prometheus et Grafana.
#
# Usage : ./trafic.sh [normal|erreur] [durée en secondes]
#   ./trafic.sh                -> 60 s de trafic normal
#   ./trafic.sh erreur 120     -> 120 s de trafic normal + des appels à /simulate-error
#
# En mode erreur, 1 requête sur 5 part sur /simulate-error : environ 20 % d'erreurs, bien au-dessus
# du seuil de l'alerte (5 %).

set -euo pipefail

MODE="${1:-normal}"
DUREE="${2:-60}"
URL="${URL:-http://localhost:5000}"

if [ "$MODE" = "erreur" ]; then
    ENDPOINTS=(/health /status /visits /status /simulate-error)
else
    ENDPOINTS=(/health /status /visits)
fi

echo "Trafic '$MODE' vers $URL pendant $DUREE s (Ctrl+C pour arrêter)"
FIN=$((SECONDS + DUREE))
while [ "$SECONDS" -lt "$FIN" ]; do
    for e in "${ENDPOINTS[@]}"; do
        curl -s -o /dev/null "$URL$e" || true
    done
    sleep 0.2
done
echo "Terminé"
