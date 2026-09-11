"""
Téléchargement d'un dossier Google Drive public via gdown.
Le dossier doit être partagé en "Tout le monde avec le lien peut voir".
"""

from pathlib import Path
import gdown


async def telecharger_dossier_drive(drive_url: str, project_id: str) -> Path:
    """
    Télécharge un dossier Drive public dans le dossier photos du projet.

    Args:
        drive_url  : URL de partage Drive (ex: https://drive.google.com/drive/folders/1AbC...)
        project_id : identifiant du projet

    Returns:
        Path vers le dossier des photos téléchargées
    """
    from projects import PROJECT_DIR
    output_dir = PROJECT_DIR / project_id / "photos"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Drive] Téléchargement de {drive_url} → {output_dir}")
    gdown.download_folder(
        url=drive_url,
        output=str(output_dir),
        quiet=False,
        use_cookies=False,
    )
    print(f"[Drive] ✅ Téléchargement terminé")
    return output_dir
