"use client";

import { useState } from "react";
import WebcamCapture from "@/components/mes-photos/WebcamCapture";
import Galerie from "@/components/mes-photos/Galerie";

export type Photo = {
  photo: string;
  distance: number;
  url: string;
};

type Statut = "idle" | "checking" | "ready" | "loading" | "done" | "error";

export default function MesPhotosPage() {
  const [codeProjet, setCodeProjet] = useState("");
  const [projetValide, setProjetValide] = useState(false);
  const [photos, setPhotos]         = useState<Photo[]>([]);
  const [statut, setStatut]         = useState<Statut>("idle");
  const [erreur, setErreur]         = useState<string | null>(null);

  const validerProjet = async () => {
    if (!codeProjet.trim()) return;
    setStatut("checking");
    setErreur(null);

    try {
      const res = await fetch(`/api-backend/projects/${codeProjet.trim()}/status`);
      if (!res.ok) throw new Error("Projet introuvable");
      const data = await res.json();
      if (data.status !== "ready") throw new Error(`Projet pas encore prêt (${data.status})`);
      setProjetValide(true);
      setStatut("ready");
    } catch (e: unknown) {
      setErreur(e instanceof Error ? e.message : "Code invalide");
      setStatut("idle");
    }
  };

  const handleSelfie = async (blob: Blob) => {
    setStatut("loading");
    setErreur(null);
    setPhotos([]);

    const formData = new FormData();
    formData.append("file", blob, "selfie.jpg");

    try {
      const res = await fetch(`/api-backend/projects/${codeProjet.trim()}/search`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Erreur ${res.status}`);
      }
      const data = await res.json();
      setPhotos(data.photos);
      setStatut("done");
    } catch (e: unknown) {
      setErreur(e instanceof Error ? e.message : "Erreur inconnue");
      setStatut("error");
    }
  };

  const handleTelechargerTout = async () => {
    for (const photo of photos) {
      const url = photo.url.startsWith("http") ? photo.url : `/api-backend${photo.url}`;
      const res  = await fetch(url);
      const blob = await res.blob();
      const obj  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = obj; a.download = photo.photo;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(obj);
      await new Promise((r) => setTimeout(r, 300));
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-white px-4 py-12">
      <div className="max-w-3xl mx-auto">

        {/* En-tête */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold tracking-tight mb-2">Retrouve tes photos</h1>
          <p className="text-zinc-400 text-base">
            Entre le code de ton événement, puis prends un selfie.
          </p>
        </div>

        {/* Saisie du code projet */}
        {!projetValide ? (
          <div className="flex flex-col items-center gap-4 mb-10">
            <div className="flex w-full max-w-sm gap-2">
              <input
                type="text"
                value={codeProjet}
                onChange={(e) => setCodeProjet(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && validerProjet()}
                placeholder="Code de l'événement…"
                className="flex-1 bg-zinc-900 border border-zinc-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-zinc-400"
              />
              <button
                onClick={validerProjet}
                disabled={statut === "checking"}
                className="bg-white text-zinc-950 font-semibold px-5 py-2.5 rounded-xl hover:bg-zinc-200 transition-colors disabled:opacity-50"
              >
                {statut === "checking" ? "…" : "OK"}
              </button>
            </div>
            {erreur && (
              <p className="text-red-400 text-sm">{erreur}</p>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center gap-2 mb-8">
            <span className="text-zinc-400 text-sm">Événement :</span>
            <span className="text-white font-semibold text-sm">{codeProjet}</span>
            <button
              onClick={() => { setProjetValide(false); setPhotos([]); setStatut("idle"); }}
              className="text-zinc-500 text-xs underline ml-2"
            >
              changer
            </button>
          </div>
        )}

        {/* Webcam */}
        {projetValide && (
          <WebcamCapture onCapture={handleSelfie} loading={statut === "loading"} />
        )}

        {/* États */}
        {statut === "loading" && (
          <div className="mt-10 text-center text-zinc-400 animate-pulse">Analyse en cours…</div>
        )}
        {statut === "error" && (
          <div className="mt-10 p-4 rounded-xl bg-red-950 border border-red-800 text-red-300 text-sm text-center">
            {erreur}
          </div>
        )}
        {statut === "done" && photos.length === 0 && (
          <div className="mt-10 text-center text-zinc-400">
            Aucune photo trouvée — essaie avec un selfie mieux éclairé.
          </div>
        )}

        {/* Résultats */}
        {statut === "done" && photos.length > 0 && (
          <div className="mt-10">
            <div className="flex items-center justify-between mb-6">
              <p className="text-zinc-400 text-sm">
                {photos.length} photo{photos.length > 1 ? "s" : ""} trouvée{photos.length > 1 ? "s" : ""}
              </p>
              <button
                onClick={handleTelechargerTout}
                className="text-sm bg-white text-zinc-950 font-semibold px-4 py-2 rounded-lg hover:bg-zinc-200 transition-colors"
              >
                Tout télécharger
              </button>
            </div>
            <Galerie photos={photos} />
          </div>
        )}

      </div>
    </main>
  );
}
