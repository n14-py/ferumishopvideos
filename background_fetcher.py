# -*- coding: utf-8 -*-
"""Descarga de videos/fotos de producto para Shorts Ferumishop."""

import os
import time
import random
import logging
import shutil
import requests
import subprocess
import urllib.parse
from config import *

logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "TU_CLAVE_PEXELS_AQUI")
_historial_pexels = []

VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _is_video_ref(ref):
    clean = (ref or "").split("?")[0].lower()
    return clean.endswith(VIDEO_EXTS)


def sanitizar_imagen(ruta_archivo):
    clean_path = ruta_archivo + "_clean.jpg"
    cmd = [
        "ffmpeg", "-y", "-v", "fatal", "-i", ruta_archivo,
        "-vf", "scale='min(1920,iw)':-2",
        "-frames:v", "1",
        clean_path,
    ]
    try:
        subprocess.run(cmd, timeout=15, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(clean_path, ruta_archivo)
        return True
    except Exception:
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
        if os.path.exists(clean_path):
            os.remove(clean_path)
        return False


def sanitizar_video(ruta_archivo):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=nw=1:nk=1",
        ruta_archivo,
    ]
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        return "video" in (resultado.stdout or "").lower()
    except Exception:
        return False


def _copy_local(ref, save_path):
    local = ref.replace("file://", "")
    if os.path.isfile(local):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        shutil.copy2(local, save_path)
        return save_path if os.path.getsize(save_path) > 100 else None
    return None


def _download_url(url, save_path, retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
    }
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=40)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(1024 * 256):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
                    return save_path
        except Exception as e:
            logger.warning("  [Fetcher] Intento %s falló: %s", attempt + 1, e)
        time.sleep(0.8)
    return None


def obtener_media(ref, save_path):
    """Acepta URL http(s) o ruta local de video/foto."""
    if not ref:
        return None
    logger.info("  [Fetcher] Media: %s", str(ref)[:80])

    local = _copy_local(ref, save_path)
    if local:
        return local

    downloaded = _download_url(ref, save_path)
    if not downloaded:
        logger.error("  [Fetcher] No se pudo bajar: %s", ref[:80])
        return None

    if _is_video_ref(ref) or save_path.lower().endswith(VIDEO_EXTS):
        if sanitizar_video(downloaded):
            return downloaded
        logger.warning("  [Fetcher] El archivo no es un video válido.")
        try:
            os.remove(downloaded)
        except OSError:
            pass
        return None

    if sanitizar_imagen(downloaded):
        return downloaded
    # Si el "jpg" era en realidad un video sin extensión
    if sanitizar_video(downloaded):
        return downloaded
    return None


def obtener_imagen_noticia(url, save_path, retries=3):
    """Alias de compatibilidad con el JSON viejo (image_url)."""
    return obtener_media(url, save_path)


def obtener_video_stock(termino_busqueda, save_path):
    """Respaldo opcional: B-roll vertical de Pexels si la IA manda type=pexels."""
    global _historial_pexels
    logger.info("  [Fetcher] Pexels vertical: '%s'", termino_busqueda)

    if PEXELS_API_KEY == "TU_CLAVE_PEXELS_AQUI":
        logger.warning("  [Fetcher] No hay PEXELS_API_KEY. Saltando stock.")
        return None

    try:
        query = urllib.parse.quote(termino_busqueda)
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=15"
        response = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, timeout=12)
        data = response.json()
        videos = data.get("videos") or []
        if not videos:
            return None

        disponibles = [v for v in videos if v.get("id") not in _historial_pexels] or videos
        elegido = random.choice(disponibles)
        _historial_pexels.append(elegido["id"])
        if len(_historial_pexels) > 50:
            _historial_pexels.pop(0)

        files = elegido.get("video_files") or []
        files.sort(key=lambda x: x.get("height", 0), reverse=True)
        video_link = None
        for file in files:
            if file.get("link") and file.get("height", 0) >= 1280:
                video_link = file["link"]
                break
        if not video_link and files:
            video_link = files[0].get("link")
        if not video_link:
            return None

        r = requests.get(video_link, stream=True, timeout=40)
        if r.status_code != 200:
            return None
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024 and sanitizar_video(save_path):
            return save_path
        if os.path.exists(save_path):
            os.remove(save_path)
        return None
    except Exception as e:
        logger.error("  [Fetcher] Error Pexels: %s", e)
        return None
