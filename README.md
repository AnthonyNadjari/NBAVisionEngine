# NBAVision Engine

Moteur d’automatisation orienté **visibilité Twitter NBA** : identification de tweets à potentiel viral intermédiaire, réponse pertinente via LLM, maximisation des visites profil tout en minimisant les risques de restriction.

**GitHub Only – 100% Free – Principal Account Safe.**

## Prérequis

- Python 3.11
- Secrets GitHub : `TWITTER_COOKIES_JSON`, `LLM_API_KEY` (ex. [Groq](https://console.groq.com) free tier)

## Installation

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

## Configuration

1. **Cookies Twitter**  
   Exportez les cookies de votre session Twitter (navigateur) au format JSON array. Voir **[docs/COOKIES.md](docs/COOKIES.md)** pour le pas-à-pas (extensions Cookie-Editor / EditThisCookie, format attendu, où mettre la valeur en local et dans le secret GitHub `TWITTER_COOKIES_JSON`).

2. **LLM**  
   Clé API Groq (free tier) : variable `LLM_API_KEY`. En local, mettez-la dans un fichier `.env` (non versionné). Sur GitHub Actions, ajoutez un secret de dépôt **LLM_API_KEY** (Settings → Secrets and variables → Actions). Optionnel : `LLM_MODEL` (défaut : `llama-3.1-8b-instant`).

## Exécution

- **Local :**  
  `python main.py` (après avoir défini les variables d’environnement ou un `.env`).

- **GitHub Actions :**  
  Workflow `NBAVision Engine` (déclenché manuellement ou par cron). Runtime max 6 h.

## Limites de session

- Max 30 réponses par session, 1 par auteur.
- Cycle toutes les ~5 minutes avec jitter.
- Arrêt après 3 erreurs consécutives ou 2 échecs de post.

## Logs

Les sessions sont enregistrées dans `logs/session_<timestamp>.json` (et en artefact du workflow si exécution GitHub Actions).

## GitHub Pages — Control Center

Une page de contrôle est fournie pour orchestrer le moteur et voir le statut en temps (quasi) réel.

1. Activer GitHub Pages : **Settings → Pages → Source** = branch **main**, dossier **/docs** (ou **root** si vous déplacez `index.html` à la racine).
2. Ouvrir `https://<votre-username>.github.io/<nom-du-repo>/` (ex. `https://nadja.github.io/NBAVisionEngine/`).
3. Optionnel : saisir un **Personal Access Token** GitHub (scope `repo`) et l’enregistrer pour **déclencher le workflow** et **rafraîchir le statut** des runs depuis la page. Le token reste uniquement dans le navigateur (session).
4. Voir aussi la section *How to export Twitter cookies* sur la page.
