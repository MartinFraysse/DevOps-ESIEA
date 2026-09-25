# Atelier 5 — Observabilité (Prometheus & Grafana)

Point de départ : copie de l'atelier 4, sans métriques pour l'instant.

Le blue/green de l'atelier 4 est maintenant dans `docker-compose.deploy.yml` (c'est lui que `deploy/deploy.sh`
utilise). `docker-compose.yml` sert à lancer l'app en local, et on y ajoutera Prometheus et Grafana.

```bash
cd atelier-5
docker compose up -d --build
curl localhost:5000/health
```
