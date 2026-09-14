# -*- coding: utf-8 -*-
"""
Orquestador Ferumishop: recibe el JSON de la IA y fabrica el Short.
Mismo contrato general que Noticias LAT (article_id, scenes, youtube_*),
pero las escenas son video tras video. Mapa / plantillas / tensión no se usan.
"""

import os
import uuid
import logging
import gc
import subprocess

from config import *
import media_manager
import background_fetcher
import tts_engine
import scene_templates.ffmpeg_clip as ffmpeg_clip

logger = logging.getLogger(__name__)

CLIP_TYPES = {
    "video", "clip", "body", "pexels", "intro",
    "ad_video", "ad_mencion", "product", "foto", "image",
}
SKIP_TYPES = {"mapa", "map"}

MEDIA_KEYS = (
    "video_url", "media_url", "clip_url", "ad_media_url",
    "url", "video", "image_url",
)
TEXT_PANTALLA_KEYS = (
    "texto_pantalla", "overlay_text", "on_screen_text",
    "screen_text", "texto_en_pantalla", "caption", "titulo_pantalla",
)
WHATSAPP_KEYS = (
    "whatsapp", "whatsapp_number", "numero_whatsapp",
    "wa", "telefono", "phone",
)


def _first(data, keys, default=""):
    if not data:
        return default
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def extraer_whatsapp(payload, scene=None):
    return (
        _first(scene, WHATSAPP_KEYS)
        or _first(payload, WHATSAPP_KEYS)
        or DEFAULT_WHATSAPP
    )


def extraer_texto_pantalla(scene, payload):
    text = _first(scene, TEXT_PANTALLA_KEYS) or _first(payload, TEXT_PANTALLA_KEYS)
    if text:
        return text
    return payload.get("youtube_title") or ""


def extraer_media_ref(scene):
    if not scene:
        return None
    for key in MEDIA_KEYS:
        value = scene.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict) and value.get("url"):
            return str(value.get("url")).strip()
    return None


def _generar_silencio(path, segundos=3.0):
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo",
        "-t", str(segundos), "-q:a", "9", "-acodec", "libmp3lame",
        path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    return path if os.path.exists(path) else None


def _fallback_fondo(save_path):
    logo = ffmpeg_clip._logo_file()
    if logo and os.path.exists(logo):
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", logo,
            "-f", "lavfi", "-i", f"color=c=0x1a0010:s={RESOLUTION_W}x{RESOLUTION_H}:r={FPS}",
            "-filter_complex",
            f"[1:v][0:v]overlay=(W-w)/2:(H-h)/2:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-t", "4", "-frames:v", "1", save_path,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
            return save_path
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x2a0a18:s={RESOLUTION_W}x{RESOLUTION_H}:d=1",
        "-frames:v", "1", save_path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    return save_path if os.path.exists(save_path) else None


def resolver_fondo(scene, idx, unique_id, archivos_temporales, ultimo_fondo):
    """Prioridad: video/foto de la IA → Pexels (si mandan termino) → clip anterior → logo."""
    ref = extraer_media_ref(scene)
    if ref:
        dest = os.path.join(
            TEMP_VIDEO_DIR if ref.lower().split("?")[0].endswith((".mp4", ".mov", ".webm", ".mkv", ".avi"))
            else TEMP_IMG_DIR,
            f"media_{unique_id}_{idx}{os.path.splitext(ref.split('?')[0])[1] or '.bin'}",
        )
        local = background_fetcher.obtener_media(ref, dest)
        if local:
            archivos_temporales.append(local)
            return local

    scene_type = (scene.get("type") or "").lower()
    termino = scene.get("termino_busqueda") or scene.get("query")
    if scene_type == "pexels" and termino:
        dest = os.path.join(TEMP_VIDEO_DIR, f"pexels_{unique_id}_{idx}.mp4")
        local = background_fetcher.obtener_video_stock(termino, dest)
        if local:
            archivos_temporales.append(local)
            return local

    if ultimo_fondo and os.path.exists(ultimo_fondo):
        logger.info("  [Orchestrator] Reusando el clip anterior (la escena no trajo media).")
        return ultimo_fondo

    dest = os.path.join(TEMP_IMG_DIR, f"fallback_{unique_id}_{idx}.jpg")
    local = _fallback_fondo(dest)
    if local:
        archivos_temporales.append(local)
    return local


def process_video_payload(payload):
    article_id = payload.get("article_id") or payload.get("product_id") or "NO_ID"
    scenes = payload.get("scenes") or []

    # Atajo: la IA puede mandar una lista plana de videos
    if not scenes and payload.get("videos"):
        overlay = extraer_texto_pantalla({}, payload)
        scenes = []
        for item in payload.get("videos") or []:
            if isinstance(item, str):
                scenes.append({"type": "video", "video_url": item, "texto_pantalla": overlay})
            elif isinstance(item, dict):
                scene = dict(item)
                scene.setdefault("type", "video")
                scenes.append(scene)

    if not scenes:
        logger.error("  [Orchestrator] El JSON no trae escenas ni videos.")
        return None

    unique_id = uuid.uuid4().hex[:8]
    final_output_path = os.path.join(OUTPUT_DIR, f"{article_id}_SHORT.mp4")
    thumbnail_output_path = os.path.join(OUTPUT_DIR, f"{article_id}_SHORT.jpg")

    archivos_temporales = []
    escenas_renderizadas = []
    miniatura_creada = False
    ultimo_fondo = None
    whatsapp = extraer_whatsapp(payload)

    logger.info("========== FERUMISHOP SHORT %s | %s escenas ==========", article_id, len(scenes))

    try:
        for idx, scene in enumerate(scenes):
            scene_type = str(scene.get("type") or "video").lower().strip()
            logger.info("  --- Clip %s/%s (%s) ---", idx + 1, len(scenes), scene_type)

            if scene_type in SKIP_TYPES and not extraer_media_ref(scene):
                logger.info("  [Orchestrator] Escena mapa ignorada (Ferumishop no usa mapas).")
                continue
            if scene_type not in CLIP_TYPES and not extraer_media_ref(scene) and not scene.get("text"):
                logger.warning("  [Orchestrator] Tipo '%s' desconocido y sin media. Saltando.", scene_type)
                continue

            fondo_path = resolver_fondo(scene, idx, unique_id, archivos_temporales, ultimo_fondo)
            if not fondo_path:
                logger.error("  [Orchestrator] Sin fondo para el clip %s. Saltando.", idx)
                continue
            ultimo_fondo = fondo_path

            texto_guion = (scene.get("text") or "").strip()
            audio_path = None
            if scene_type != "ad_video" and texto_guion:
                audio_filename = f"audio_{unique_id}_{idx}.mp3"
                voz = scene.get("voice") or DEFAULT_VOICE
                audio_path = tts_engine.generate_audio_clip(texto_guion, voz, audio_filename)
                if audio_path:
                    archivos_temporales.append(audio_path)
            if not audio_path:
                audio_filename = f"audio_{unique_id}_{idx}_silencio.mp3"
                audio_path = os.path.join(TEMP_AUDIO_DIR, audio_filename)
                segundos = 5.0 if scene_type == "ad_video" else 3.0
                audio_path = _generar_silencio(audio_path, segundos)
                if audio_path:
                    archivos_temporales.append(audio_path)

            texto_pantalla = extraer_texto_pantalla(scene, payload)
            wa_clip = extraer_whatsapp(payload, scene)
            escena_output = os.path.join(TEMP_VIDEO_DIR, f"escena_{unique_id}_{idx}.mp4")

            exito = ffmpeg_clip.renderizar_clip(
                fondo_path=fondo_path,
                audio_tts_path=audio_path,
                texto_pantalla=texto_pantalla,
                whatsapp_text=wa_clip,
                sfx_path=None,
                output_path=escena_output,
            )

            if exito and os.path.exists(escena_output):
                escenas_renderizadas.append(escena_output)
                archivos_temporales.append(escena_output)
                if not miniatura_creada:
                    try:
                        cmd_thumb = [
                            "ffmpeg", "-y", "-ss", "00:00:01.2", "-i", escena_output,
                            "-vframes", "1", "-q:v", "2", thumbnail_output_path,
                        ]
                        subprocess.run(cmd_thumb, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        miniatura_creada = os.path.exists(thumbnail_output_path)
                    except Exception:
                        pass
            else:
                logger.error("  [Orchestrator] Falló el clip %s (%s).", idx, scene_type)

        if not escenas_renderizadas:
            logger.error("  [Orchestrator] No se renderizó ningún clip.")
            return None

        whooshes = media_manager.list_whoosh_files()
        exito_final = ffmpeg_clip.concatenar_con_transiciones(
            escenas_renderizadas, final_output_path, whoosh_paths=whooshes
        )
        if exito_final:
            logger.info("========== SHORT FERUMI LISTO: %s ==========", final_output_path)
            return final_output_path

        logger.error("  [Orchestrator] Falló el ensamblado final.")
        return None

    except Exception as e:
        logger.error("  [Orchestrator] ERROR FATAL: %s", e)
        return None
    finally:
        logger.info("  [Orchestrator] Limpiando temporales...")
        for archivo in archivos_temporales:
            try:
                if archivo and os.path.exists(archivo):
                    os.remove(archivo)
            except Exception:
                pass
        gc.collect()
