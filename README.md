# NBAVision Engine

Moteur d'automatisation NBA sur X (Twitter) : trouve des tweets, répond avec des templates (ou IA si configuré). **100 % gratuit.**

**Tout s’exécute sur GitHub** (pas sur votre PC). Une fois les secrets configurés, le moteur tourne deux fois par jour (9h et 16h UK) ou peut être lancé à la main depuis Actions.

---

## Tutoriel (tout en un)

→ **[docs/TUTORIAL.md](docs/TUTORIAL.md)** — planning, configuration des secrets, dashboard affichage seul, et comment lancer une exécution.

---

## En bref

| Question | Réponse |
|----------|--------|
| Où est le planning ? | Fichier `.github/workflows/nbavision.yml` (cron 9h et 16h UK = 09:00 et 16:00 UTC). |
| Ça tourne sur mon PC ? | **Non.** Sur les serveurs GitHub. |
| À faire une fois | Ajouter le secret `TWITTER_COOKIES_JSON` (voir [docs/SECRETS-SETUP.md](docs/SECRETS-SETUP.md)). |
| Lancer à la main ? | Repo → **Actions** → **NBAVision Engine** → **Run workflow**. |

---

## Liens

- [Tutoriel complet](docs/TUTORIAL.md)
- [Secrets GitHub Actions](docs/SECRETS-SETUP.md)
- **Dashboard (affichage seul)** : [GitHub Pages](https://anthonynadjari.github.io/NBAVisionEngine/) — ouvrir la page avec un token dans l’URL (`#ghp_...`) pour voir le dernier run, les stats et les tweets postés.
