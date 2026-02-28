# NBAVision Engine

Moteur d’automatisation orienté **visibilité Twitter NBA** : identification de tweets à potentiel viral intermédiaire, réponse pertinente via LLM, maximisation des visites profil tout en minimisant les risques de restriction.

**GitHub Only – 100% Free – Principal Account Safe.**

## Prérequis

- Python 3.11
- Fichier **`credentials.json`** à la racine du projet (cookies X + clé API LLM)

## Installation

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

## Configuration

Tout se trouve dans **`credentials.json`** à la racine du repo (pas de variables secrètes GitHub) :

```json
{
  "llm_api_key": "ta_clé_groq",
  "llm_model": "llama-3.1-8b-instant",
  "twitter_cookies": [ { "name": "auth_token", "value": "...", "domain": ".x.com", "path": "/", ... }, ... ]
}
```

- **Cookies X** : export depuis le navigateur (Cookie-Editor / EditThisCookie) → tableau JSON dans `twitter_cookies`. Voir **[docs/SECRETS-SETUP.md](docs/SECRETS-SETUP.md)** pour GitHub Actions.
- **LLM** (optionnel) : sans clé = réponses template. Avec clé Groq dans `llm_api_key` = réponses IA.

Les variables d’environnement (`TWITTER_COOKIES_JSON`, `LLM_API_KEY`, etc.) restent supportées en secours si le fichier n’est pas présent.

## Exécution

- **Local :**  
  `python main.py` (lit `credentials.json` automatiquement).

- **GitHub Actions :**  
  Workflow `NBAVision Engine` (déclenché manuellement ou par cron). Runtime max 6 h.  
  **Ne pas committer `credentials.json`.** Configurer les **secrets du dépôt** : **Settings → Secrets and variables → Actions** :
  - **`TWITTER_COOKIES_JSON`** : tableau JSON des cookies X (exporter depuis le navigateur, même format que `twitter_cookies` dans `credentials.json`).
  - **`LLM_API_KEY`** (optionnel) : clé Groq pour réponses IA. Sans = templates.
  - **`LLM_MODEL`** (optionnel) : ex. `llama-3.1-8b-instant`.

## Durée de vie des cookies (GitHub Actions)

Quand le workflow tourne sur GitHub Actions, l’IP est celle d’un datacenter. X/Twitter peut considérer la session comme suspecte et l’invalider après quelques runs, ce qui oblige à **ré-exporter les cookies** de temps en temps. Ce n’est pas un bug du moteur.

**Pour limiter les ré-exports :**
- **Réduire la fréquence** : passer le cron (dans `.github/workflows/nbavision.yml`) à une fois par semaine au lieu de tous les jours (ex. `cron: "0 14 * * 0"` = dimanche 14h).
- **Lancer en local** : exécuter `python main.py` sur votre PC (même IP / même « appareil » qu’au moment de l’export) ; les cookies tiennent généralement plus longtemps.
- Ré-exporter les cookies uniquement lorsque le workflow échoue avec *« Cookies present but session invalid or expired »*.

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
