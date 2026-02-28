# NBAVision Engine — Tutoriel complet

Moteur d’automatisation NBA sur X (Twitter) : trouve des tweets, répond avec des templates (ou IA si configuré). **100 % gratuit, pas de Groq obligatoire.**

---

## Deux modes possibles

| Mode | Où ça tourne | Cookies | Réponses |
|------|--------------|---------|----------|
| **Local (webhook)** | Votre PC | Profil persistant (connexion une fois) | Templates (ou Groq si configuré) |
| **GitHub Actions** | Cloud GitHub | Export cookies → secret | Templates (ou Groq si configuré) |

**Recommandé : mode local** — pas d’export de cookies, pas de clé API, connexion X une seule fois.

---

# Mode local (webhook) — recommandé

## Étape 1 : Ouvrir le dossier du projet

Dans PowerShell ou CMD :

```
cd C:\Users\nadja\OneDrive\Bureau\code\NBAVisionEngine\NBAVisionEngine
```

(Adaptez le chemin si votre projet est ailleurs.)

---

## Étape 2 : Installation (une fois)

```
.\setup.bat
```

Cela crée un environnement virtuel (`.venv`), installe les dépendances et Playwright Chromium.

---

## Étape 3 : Connexion à X (une fois)

```
.\login_once.bat
```

Une fenêtre de navigateur s’ouvre. Connectez-vous à X (Twitter), puis revenez au terminal et appuyez sur Entrée. Votre session est enregistrée dans `browser_profile/`. **Plus besoin d’exporter des cookies.**

---

## Étape 4 : Démarrer le serveur

```
.\run_server.bat
```

- Au premier lancement, un fichier `.env` est créé avec un secret.
- Le serveur écoute sur `http://127.0.0.1:8000`.
- Laissez cette fenêtre ouverte.

---

## Étape 5 : Exposer le webhook (tunnel)

Ouvrez **un second terminal** dans le même dossier.

### Option A : Cloudflare Tunnel (sans compte)

1. Télécharger : https://github.com/cloudflare/cloudflared/releases/latest  
   → Fichier `cloudflared-windows-amd64.exe`
2. Renommer en `cloudflared.exe` et le placer dans un dossier (ex. `C:\cloudflared\`)
3. Lancer :

```
C:\cloudflared\cloudflared.exe tunnel --url http://localhost:8000
```

Vous obtenez une URL du type `https://xxxx.trycloudflare.com`.

### Option B : ngrok (compte gratuit)

1. Créer un compte : https://dashboard.ngrok.com/signup
2. Récupérer l’authtoken : https://dashboard.ngrok.com/get-started/your-authtoken
3. Configurer une fois : `ngrok config add-authtoken VOTRE_TOKEN`
4. Lancer : `ngrok http 8000`

Utilisez l’URL HTTPS affichée (ex. `https://abc123.ngrok-free.app`).

---

## Étape 6 : Déclencher une exécution

**Depuis un navigateur ou Postman :**

```
POST https://VOTRE_URL_TUNNEL/trigger
Header: X-API-KEY: <votre secret>
```

Le secret est dans le fichier `.env` (ligne `NBAVISION_SECRET=...`).

**Exemple avec PowerShell :**

```powershell
$secret = (Get-Content .env | Where-Object { $_ -match "NBAVISION_SECRET=" }) -replace "NBAVISION_SECRET=", ""
Invoke-RestMethod -Uri "https://VOTRE_URL/trigger" -Method POST -Headers @{ "X-API-KEY" = $secret }
```

**Exemple avec curl :**

```bash
curl -X POST https://VOTRE_URL/trigger -H "X-API-KEY: votre_secret"
```

---

## Résumé mode local

| Étape | Commande |
|-------|----------|
| 1 | `cd` vers le dossier du projet |
| 2 | `.\setup.bat` |
| 3 | `.\login_once.bat` → connexion X → Entrée |
| 4 | `.\run_server.bat` (fenêtre 1) |
| 5 | `cloudflared tunnel --url http://localhost:8000` ou `ngrok http 8000` (fenêtre 2) |
| 6 | `POST /trigger` avec header `X-API-KEY` |

---

# Mode GitHub Actions

Pour exécuter le moteur dans le cloud (sans PC allumé).

## Prérequis

- Un secret **`TWITTER_COOKIES_JSON`** (tableau JSON des cookies X)
- **`LLM_API_KEY`** et **`LLM_MODEL`** optionnels (sans = templates)

## Configuration des secrets

1. Aller sur : https://github.com/AnthonyNadjari/NBAVisionEngine/settings/secrets/actions
2. **Nouveau secret** → Nom : `TWITTER_COOKIES_JSON`
3. Valeur : exporter les cookies depuis x.com (extension Cookie-Editor) → copier uniquement le tableau `[...]`
4. (Optionnel) **Nouveau secret** → `LLM_API_KEY` → clé Groq si vous voulez des réponses IA

Voir **[SECRETS-SETUP.md](SECRETS-SETUP.md)** pour le détail.

## Lancer un run

- **Actions** → **NBAVision Engine** → **Run workflow**

Le workflow tourne une fois par semaine (dimanche 14h UTC). Vous pouvez aussi le lancer manuellement.

---

# Control Center (GitHub Pages)

Page web pour voir le statut et déclencher le workflow GitHub Actions.

1. **Settings** → **Pages** → Source : branch **main**, dossier **/docs**
2. Ouvrir `https://anthonynadjari.github.io/NBAVisionEngine/`
3. Pour déclencher le workflow : ouvrir une fois avec `#ghp_VOTRE_TOKEN` dans l’URL (token GitHub avec scope `repo`)

---

# Dépannage

| Problème | Solution |
|----------|----------|
| `cloudflared` introuvable | Utiliser le chemin complet vers `cloudflared.exe` ou l’ajouter au PATH |
| ngrok 4018 | Créer un compte et configurer l’authtoken |
| Session X invalide | Relancer `.\login_once.bat` et se reconnecter |
| 409 Conflict | Un run est déjà en cours, attendre la fin |
| 401 Unauthorized | Vérifier que `X-API-KEY` correspond au secret dans `.env` |

---

# Fichiers importants

| Fichier | Rôle |
|---------|------|
| `setup.bat` | Installation (venv + deps + Playwright) |
| `login_once.bat` | Connexion X une fois (profil persistant) |
| `run_server.bat` | Démarrage du serveur webhook |
| `.env` | Secret pour le webhook (créé au 1er run) |
| `browser_profile/` | Session X (ne pas supprimer) |
