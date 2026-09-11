import asyncio
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
from PIL import Image

from auth import get_current_user
from config import settings
from projects import (
    creer_projet, get_projet, lister_projets,
    set_status, get_status, PROJECT_DIR
)
from embeddings import generer_embeddings   # ← BLOC 1
from search import rechercher               # ← BLOC 2
from drive_download import telecharger_dossier_drive

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Face Search API — Multi-projets", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sert les photos locales (dev mode)
if settings.DEV_MODE:
    app.mount(
        "/photos",
        StaticFiles(directory=str(PROJECT_DIR), follow_symlink=True),
        name="photos"
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
    background_tasks: BackgroundTasks,
    nom: str,
    drive_url: str,
    user=Depends(get_current_user),
):
    """
    Crée un nouveau projet :
    1. Télécharge le dossier Drive
    2. Lance la génération des embeddings en arrière-plan (BLOC 1)
    """
    projet = creer_projet(nom)
    if projet is None:
        raise HTTPException(status_code=400, detail=f"Projet '{nom}' existe déjà")

    background_tasks.add_task(_pipeline_creation, projet["id"], drive_url)
    return {"message": "Projet créé, génération des embeddings en cours", "projet": projet}


async def _pipeline_creation(project_id: str, drive_url: str):
    """Tâche de fond : téléchargement + génération embeddings."""
    try:
        set_status(project_id, "downloading")
        photos_dir = await telecharger_dossier_drive(drive_url, project_id)

        set_status(project_id, "processing")
        # ▼▼▼ BLOC 1 : génération des embeddings ▼▼▼
        nb = await asyncio.to_thread(generer_embeddings, project_id, photos_dir)
        # ▲▲▲ FIN BLOC 1 ▲▲▲

        set_status(project_id, "ready", nb_embeddings=nb)
    except Exception as e:
        set_status(project_id, "error", erreur=str(e))


@app.get("/projects/{project_id}/status")
def project_status(project_id: str, user=Depends(get_current_user)):
    """Retourne le statut d'un projet (downloading / processing / ready / error)."""
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
    Reçoit un selfie et retourne les photos du projet où ce visage apparaît.
    ← BLOC 2 : détection (voir search.py)
    """
    status = get_status(project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    if status["status"] != "ready":
        raise HTTPException(status_code=425, detail=f"Projet pas encore prêt ({status['status']})")

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide")

    # ▼▼▼ BLOC 2 : recherche / détection ▼▼▼
    resultats = rechercher(img, project_id, seuil)
    # ▲▲▲ FIN BLOC 2 ▲▲▲

    if resultats is None:
        raise HTTPException(status_code=422, detail="Aucun visage détecté dans le selfie")

    return {"count": len(resultats), "photos": resultats}
