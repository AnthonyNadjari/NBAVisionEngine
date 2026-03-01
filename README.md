# NBAVision Engine

Moteur d'automatisation NBA sur X (Twitter) : trouve des tweets, répond avec des templates (ou IA si configuré). **100 % gratuit.**

**Tout s’exécute sur GitHub** (pas sur votre PC). Une fois les secrets configurés, le moteur peut tourner chaque dimanche à 14h UTC ou être lancé à la main.

---

## Tutoriel (tout en un)

→ **[docs/TUTORIAL.md](docs/TUTORIAL.md)** — où est le planning hebdo, configuration des secrets, Control Center, et comment lancer une exécution.

---

## En bref

| Question | Réponse |
|----------|--------|
| Où est le planning hebdo ? | Fichier `.github/workflows/nbavision.yml` (cron dimanche 14h UTC). |
| Ça tourne sur mon PC ? | **Non.** Sur les serveurs GitHub. |
| À faire une fois | Ajouter le secret `TWITTER_COOKIES_JSON` (voir [docs/SECRETS-SETUP.md](docs/SECRETS-SETUP.md)). |

---

## Liens

- [Tutoriel complet](docs/TUTORIAL.md)
- [Secrets GitHub Actions](docs/SECRETS-SETUP.md)
- Control Center : ouvrir `docs/index.html` avec un token dans l’URL (`#ghp_...`) pour voir le statut et lancer une exécution.
