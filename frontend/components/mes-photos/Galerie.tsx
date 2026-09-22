"use client";

import { useState } from "react";
import type { Photo } from "@/app/mes-photos/page";

export default function Galerie({ photos }: { photos: Photo[] }) {
  const [selectionnee, setSelectionnee] = useState<Photo | null>(null);

  // Gère les URLs externes (Pixieset) et internes (/projects/...)
  const toDisplayUrl = (url: string) =>
    url.startsWith("http") ? url : `/api-backend${url}`;

  const telechargerUne = async (photo: Photo) => {
    const url = toDisplayUrl(photo.url);
    try {
      const res  = await fetch(url);
      const blob = await res.blob();
      const obj  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = obj; a.download = photo.photo;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(obj);
    } catch {
      window.open(url, "_blank");
    }
  };

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {photos.map((photo) => (
          <div
            key={photo.photo}
            className="group relative aspect-square rounded-xl overflow-hidden bg-zinc-900 cursor-pointer"
            onClick={() => setSelectionnee(photo)}
          >
            <img
              src={toDisplayUrl(photo.url)}
              alt={photo.photo}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
              <button
                onClick={(e) => { e.stopPropagation(); telechargerUne(photo); }}
                className="text-xs text-white bg-white/20 backdrop-blur-sm border border-white/30 px-3 py-1.5 rounded-lg hover:bg-white/30 transition-colors"
              >
                Télécharger
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectionnee && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setSelectionnee(null)}
        >
          <div className="relative max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
            <img
              src={toDisplayUrl(selectionnee.url)}
              alt={selectionnee.photo}
              className="w-full max-h-[80vh] object-contain rounded-xl"
            />
            <div className="flex items-center justify-between mt-4">
              <p className="text-zinc-400 text-sm truncate">{selectionnee.photo}</p>
              <div className="flex gap-3">
                <button
                  onClick={() => telechargerUne(selectionnee)}
                  className="text-sm bg-white text-zinc-950 font-semibold px-4 py-2 rounded-lg hover:bg-zinc-200 transition-colors"
                >
                  Télécharger
                </button>
                <button
                  onClick={() => setSelectionnee(null)}
                  className="text-sm border border-zinc-700 text-zinc-300 px-4 py-2 rounded-lg hover:border-zinc-500 transition-colors"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
