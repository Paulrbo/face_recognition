import asyncio
import io

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from auth import get_current_user
from config import settings
from drive_download import telecharger_dossier_drive
from drive_mapping import generer_mapping_drive
from embeddings import generer_embeddings
from projects import PROJECT_DIR, creer_projet, get_status, lister_projets, photos_dir, set_status
from search import invalider_cache, rechercher

app = FastAPI(title="Face Recognition API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/projects")
def list_projects(user=Depends(get_current_user)):
    return lister_projets()


@app.post("/projects/create")
async def create_project(
    nom: str,
    drive_url: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    projet = creer_projet(nom)
    if projet is None:
        raise HTTPException(status_code=400, detail=f"Le projet '{nom}' existe déjà")
    background_tasks.add_task(_pipeline_creation, projet["id"], drive_url)
    return {"message": "Projet créé — traitement en cours", "projet": projet}


async def _pipeline_creation(project_id: str, drive_url: str):
    try:
        set_status(project_id, "downloading")
        photos_path = await telecharger_dossier_drive(drive_url, project_id)

        set_status(project_id, "processing")
        nb = await asyncio.to_thread(generer_embeddings, project_id, photos_path)

        set_status(project_id, "mapping")
        await asyncio.to_thread(generer_mapping_drive, project_id, drive_url)

        invalider_cache(project_id)
        set_status(project_id, "ready", nb_embeddings=nb)

    except Exception as e:
        set_status(project_id, "error", erreur=str(e))
        print(f"[pipeline] Erreur projet '{project_id}' : {e}")


@app.get("/projects/{project_id}/status")
def project_status(project_id: str, user=Depends(get_current_user)):
    status = get_status(project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return status


@app.get("/projects/{project_id}/photos/{filename:path}")
async def get_photo(project_id: str, filename: str, user=Depends(get_current_user)):
    """Sert une photo depuis le stockage local du projet."""
    for f in photos_dir(project_id).rglob(filename):
        return FileResponse(str(f))
    raise HTTPException(status_code=404, detail="Photo introuvable")


@app.post("/projects/{project_id}/search")
async def search(
    project_id: str,
    file: UploadFile = File(...),
    seuil: float = settings.SEUIL_DEFAULT,
    user=Depends(get_current_user),
):
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

    resultats = rechercher(img, project_id, seuil)
    if resultats is None:
        raise HTTPException(status_code=422, detail="Aucun visage détecté dans le selfie")

    return {"count": len(resultats), "photos": resultats}
