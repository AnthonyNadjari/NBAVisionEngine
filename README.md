# NBAVision Engine

Moteur d'automatisation NBA sur X (Twitter) : trouve des tweets, répond avec des templates (ou IA si configuré). **100 % gratuit.**

**Tout s’exécute sur GitHub** (via un runner sur votre PC). Une fois le runner et les secrets configurés, le moteur tourne deux fois par jour (9h et 16h UK) ou peut être lancé à la main depuis Actions.

---

## How to use (concise)

→ **[docs/HOW-TO-USE.md](docs/HOW-TO-USE.md)** — one-time setup (runner + cookies), how to run, logs, refresh cookies.

→ [docs/TUTORIAL.md](docs/TUTORIAL.md) — longer tutorial; [docs/SELF-HOSTED-RUNNER.md](docs/SELF-HOSTED-RUNNER.md) — runner setup.

---

## En bref

| Question | Réponse |
|----------|--------|
| Où est le planning ? | Fichier `.github/workflows/nbavision.yml` (cron 9h et 16h UK = 09:00 et 16:00 UTC). |
| Ça tourne sur mon PC ? | **Oui.** Runner auto-hébergé (une fois configuré) pour que les cookies X restent valides. Voir [docs/SELF-HOSTED-RUNNER.md](docs/SELF-HOSTED-RUNNER.md). |
| À faire une fois | 1) Configurer le runner auto-hébergé. 2) Ajouter le secret `TWITTER_COOKIES_JSON` ([docs/SECRETS-SETUP.md](docs/SECRETS-SETUP.md)). |
| Lancer à la main ? | Repo → **Actions** → **NBAVision Engine** → **Run workflow**. |

---

## Liens

- [Tutoriel complet](docs/TUTORIAL.md)
- [Runner auto-hébergé (setup une fois)](docs/SELF-HOSTED-RUNNER.md)
- [Secrets GitHub Actions](docs/SECRETS-SETUP.md)
- **Dashboard (affichage seul)** : [GitHub Pages](https://anthonynadjari.github.io/NBAVisionEngine/) — ouvrir la page avec un token dans l’URL (`#ghp_...`) pour voir le dernier run, les stats et les tweets postés.
