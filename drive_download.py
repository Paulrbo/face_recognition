"""
Téléchargement d'un dossier Google Drive public.
Le dossier doit être partagé en "Tout le monde avec le lien peut voir".
"""

from pathlib import Path
import gdown


async def telecharger_dossier_drive(drive_url: str, project_id: str) -> Path:
    """
    Télécharge un dossier Drive public dans models/projets/<project_id>/photos/.

    Args:
        drive_url  : URL de partage Drive (https://drive.google.com/drive/folders/...)
        project_id : identifiant du projet

    Returns:
        Path vers le dossier des photos téléchargées
    """
    from projects import photos_dir
    output = photos_dir(project_id)
    output.mkdir(parents=True, exist_ok=True)

    print(f"[Drive] Téléchargement de {drive_url} → {output}")
    gdown.download_folder(url=drive_url, output=str(output), quiet=False, use_cookies=False)
    print(f"[Drive] ✅ Téléchargement terminé")
    return output
