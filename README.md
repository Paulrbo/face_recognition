# Face Recognition API

API générique de reconnaissance faciale — trouve toutes les photos d'un dataset où une personne apparaît, à partir d'un selfie.

## Fonctionnement

1. **Créer un projet** → tu envoies un lien Google Drive public contenant des photos
2. **Attendre** → l'API télécharge les photos et génère les embeddings en arrière-plan
3. **Rechercher** → tu envoies un selfie, l'API retourne les photos où ce visage apparaît

## Structure

```
face_recognition/
├── main.py           → routes FastAPI
├── embeddings.py     → BLOC 1 : génération des embeddings (algo prétraitement)
├── search.py         → BLOC 2 : détection / recherche (algo détection)
├── projects.py       → gestion des projets (status, CSV, dossiers)
├── drive_download.py → téléchargement dossier Drive public
├── auth.py           → authentification
├── config.py         → configuration (.env)
└── models/
    └── projets/
        └── <project_id>/
            ├── status.json     → état du projet
            ├── embeddings.csv  → embeddings générés
            └── photos/         → photos téléchargées
```

## Lancer en local

```bash
# 1. Copier et remplir le .env
cp .env.example .env

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'API
python -m uvicorn main:app --reload
```

→ API disponible sur http://localhost:8000
→ Docs interactives : http://localhost:8000/docs

## Routes

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Vérification |
| GET | `/projects` | Liste des projets |
| POST | `/projects/create?nom=X&drive_url=Y` | Créer un projet |
| GET | `/projects/{id}/status` | Statut du projet |
| POST | `/projects/{id}/search` | Recherche par selfie |

## Tester sans Google Drive (dev)

Pour tester avec des photos déjà en local, crée manuellement la structure :

```
models/projets/<project_id>/
├── photos/         ← copie tes photos ici
├── embeddings.csv  ← ton CSV d'embeddings existant
└── status.json     ← {"id":"...", "nom":"...", "status":"ready", "nb_embeddings":0, "cree_le":"2026-01-01T00:00:00", "erreur":null}
```
