import asyncio
import io

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from auth import get_current_user
from config import settings
from drive_download import telecharger_dossier_drive
from embeddings import generer_embeddings
from projects import (PROJECT_DIR, creer_projet, get_status,
                      lister_projets, set_status)
from search import invalider_cache, rechercher

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Face Recognition API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# En dev, sert les photos depuis models/projets/
if settings.DEV_MODE:
    app.mount(
        "/photos",
        StaticFiles(directory=str(PROJECT_DIR), follow_symlink=True),
        name="photos",
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/projects")
def list_projects(user=Depends(get_current_user)):
    """Liste tous les projets existants."""
    return lister_projets()


@app.post("/projects/create")
async def create_project(
    nom: str,
    drive_url: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """
    Crée un projet à partir d'un dossier Google Drive public :
    1. Télécharge les photos
    2. Génère les embeddings en arrière-plan (BLOC 1)
    """
    projet = creer_projet(nom)
    if projet is None:
        raise HTTPException(status_code=400, detail=f"Le projet '{nom}' existe déjà")

    background_tasks.add_task(_pipeline_creation, projet["id"], drive_url)
    return {
        "message": "Projet créé — génération des embeddings en cours",
        "projet": projet,
    }


async def _pipeline_creation(project_id: str, drive_url: str):
    """Tâche de fond : téléchargement Drive + génération des embeddings."""
    try:
        set_status(project_id, "downloading")
        photos_path = await telecharger_dossier_drive(drive_url, project_id)

        set_status(project_id, "processing")
        nb = await asyncio.to_thread(generer_embeddings, project_id, photos_path)

        invalider_cache(project_id)
        set_status(project_id, "ready", nb_embeddings=nb)

    except Exception as e:
        set_status(project_id, "error", erreur=str(e))
        print(f"[pipeline] ❌ Erreur projet '{project_id}' : {e}")


@app.get("/projects/{project_id}/status")
def project_status(project_id: str, user=Depends(get_current_user)):
    """Statut d'un projet : created / downloading / processing / ready / error."""
    status = get_status(project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return status


@app.post("/projects/{project_id}/search")
async def search(
    project_id: str,
    file: UploadFile = File(...),
    seuil: float = settings.SEUIL_DEFAULT,
    user=Depends(get_current_user),
):
    """
    Envoie un selfie, reçoit les photos du projet où ce visage apparaît.
    ← BLOC 2 (voir search.py)
    """
    status = get_status(project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    if status["status"] != "ready":
        raise HTTPException(
            status_code=425,
            detail=f"Projet pas encore prêt (statut : {status['status']})",
        )

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide")

    resultats = rechercher(img, project_id, seuil)

    if resultats is None:
        raise HTTPException(status_code=422, detail="Aucun visage détecté dans le selfie")

    return {"count": len(resultats), "photos": resultats}