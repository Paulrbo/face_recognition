"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  onCapture: (blob: Blob) => void;
  loading: boolean;
};

export default function WebcamCapture({ onCapture, loading }: Props) {
  const videoRef  = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [actif, setActif]         = useState(false);
  const [pret, setPret]           = useState(false);
  const [apercu, setApercu]       = useState<string | null>(null);
  const [erreurCam, setErreurCam] = useState<string | null>(null);

  const demarrerCamera = useCallback(async () => {
    setErreurCam(null);
    setApercu(null);
    setPret(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 640, height: 480 },
      });
      streamRef.current = stream;
      setActif(true);
    } catch {
      setErreurCam("Impossible d'accéder à la caméra. Vérifie les permissions.");
    }
  }, []);

  useEffect(() => {
    if (actif && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [actif]);

  const arreterCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setActif(false);
    setPret(false);
  }, []);

  const prendreSelfie = useCallback(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !pret) return;

    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
    setApercu(dataUrl);
    arreterCamera();

    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob);
        else { setErreurCam("Capture échouée — réessaie."); setApercu(null); }
      },
      "image/jpeg",
      0.92
    );
  }, [onCapture, arreterCamera, pret]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-full max-w-sm aspect-[4/3] rounded-2xl overflow-hidden bg-zinc-900 border border-zinc-800">
        {actif && (
          <video
            ref={videoRef}
            autoPlay playsInline muted
            onCanPlay={() => setPret(true)}
            className="w-full h-full object-cover scale-x-[-1]"
          />
        )}
        {apercu && (
          <img src={apercu} alt="Selfie capturé" className="w-full h-full object-cover" />
        )}
        {!actif && !apercu && (
          <div className="flex items-center justify-center w-full h-full text-zinc-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M15.75 10.5a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M19.5 8.25h-1.06a2.25 2.25 0 01-1.95-1.125l-.813-1.408A2.25 2.25 0 0013.725 4.5h-3.45a2.25 2.25 0 00-1.952 1.217L7.51 7.125A2.25 2.25 0 015.56 8.25H4.5a2.25 2.25 0 00-2.25 2.25v8.25A2.25 2.25 0 004.5 21h15a2.25 2.25 0 002.25-2.25v-8.25A2.25 2.25 0 0019.5 8.25z" />
            </svg>
          </div>
        )}
      </div>

      <canvas ref={canvasRef} className="hidden" />

      {erreurCam && <p className="text-red-400 text-sm text-center max-w-xs">{erreurCam}</p>}

      {!actif && !apercu && (
        <button onClick={demarrerCamera}
          className="bg-white text-zinc-950 font-semibold px-6 py-2.5 rounded-xl hover:bg-zinc-200 transition-colors">
          Ouvrir la caméra
        </button>
      )}
      {actif && (
        <button onClick={prendreSelfie} disabled={loading || !pret}
          className="bg-white text-zinc-950 font-semibold px-6 py-2.5 rounded-xl hover:bg-zinc-200 transition-colors disabled:opacity-40">
          {pret ? "Prendre le selfie" : "Chargement caméra…"}
        </button>
      )}
      {apercu && !loading && (
        <button onClick={() => { setApercu(null); demarrerCamera(); }}
          className="border border-zinc-700 text-zinc-300 px-5 py-2.5 rounded-xl hover:border-zinc-500 transition-colors text-sm">
          Recommencer
        </button>
      )}
    </div>
  );
}
