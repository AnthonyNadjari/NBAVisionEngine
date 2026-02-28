# NBAVision Engine

Moteur d'automatisation NBA sur X (Twitter) : trouve des tweets, répond avec des templates (ou IA si configuré). **100 % gratuit.**

---

## Démarrage rapide (mode local)

```powershell
cd C:\Users\nadja\OneDrive\Bureau\code\NBAVisionEngine\NBAVisionEngine
.\setup.bat
.\login_once.bat      # Connexion X une fois
.\run_server.bat     # Serveur webhook
```

Dans un second terminal : `cloudflared tunnel --url http://localhost:8000` (ou ngrok).

Puis : `POST https://VOTRE_URL/trigger` avec header `X-API-KEY: <secret du .env>`.

---

## Tutoriel complet

→ **[docs/TUTORIAL.md](docs/TUTORIAL.md)** — tout le détail étape par étape.

---

## Modes d'exécution

| Mode | Où | Cookies | Réponses |
|------|-----|---------|----------|
| **Local (webhook)** | Votre PC | Profil persistant (connexion 1×) | Templates |
| **GitHub Actions** | Cloud | Export cookies → secret | Templates |

Pas de Groq obligatoire — templates NBA par défaut.

---

## Liens utiles

- [Tutoriel complet](docs/TUTORIAL.md)
- [Secrets GitHub Actions](docs/SECRETS-SETUP.md)
- [Webhook détaillé](docs/WEBHOOK-SETUP.md)
