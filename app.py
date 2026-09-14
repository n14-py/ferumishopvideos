# -*- coding: utf-8 -*-
"""
Servidor Flask Ferumishop Shorts.
Recibe el JSON de la IA (mismo contrato general que Noticias LAT:
article_id, scenes, youtube_title/description/tags) y fabrica un Short
1080x1920 @ 30fps: video tras video + logo + texto en pantalla + WhatsApp.

Campos extra que la IA puede enviar:
  - texto_pantalla / overlay_text / on_screen_text  (arriba al centro)
  - whatsapp / whatsapp_number                       (debajo del logo)
  - video_url / media_url / image_url por escena
  - product_id como alias de article_id
"""

import os
import threading
import gc
import logging
import requests
import subprocess
from flask import Flask, request, jsonify

import main_orchestrator
import youtube_uploader
import cloudflare_r2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "secreto123456")
MAIN_API_URL = os.getenv("MAIN_API_URL", "https://lfaftechapi.onrender.com")
PORT = int(os.getenv("PORT", 3001))

app = Flask(__name__)
processing_lock = threading.Lock()


def _check_auth():
    api_key = request.headers.get("x-api-key")
    return api_key == ADMIN_API_KEY


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "server": "Ferumishop Shorts Factory"}), 200


@app.route("/generate_video", methods=["POST"])
def handle_generate_video():
    if not _check_auth():
        logger.warning("  [API] Acceso no autorizado desde %s", request.remote_addr)
        return jsonify({"error": "No autorizado. API Key inválida."}), 403

    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No se envió un cuerpo JSON válido."}), 400

    article_id = payload.get("article_id") or payload.get("product_id")
    scenes = payload.get("scenes") or payload.get("videos")
    youtube_title = payload.get("youtube_title", "Ferumishop #Shorts")
    youtube_desc = payload.get(
        "youtube_description",
        "Comprá en ferumi.shop 💖 #ferumi #maquillaje #shorts",
    )
    youtube_tags = payload.get("youtube_tags", ["ferumi", "ferumishop", "maquillaje", "shorts"])

    if not article_id or not scenes:
        return jsonify({"error": "Faltan datos obligatorios: article_id (o product_id) y scenes."}), 400

    payload["article_id"] = article_id

    if youtube_uploader.is_already_processed(article_id):
        logger.info("  [API] Tarea %s ignorada. Ya existe en el historial.", article_id)
        return jsonify({
            "message": "El Short ya fue generado y subido anteriormente.",
            "status": "completed",
            "article_id": article_id,
        }), 200

    if processing_lock.acquire(blocking=False):
        logger.info("  [API] [Lock] Producción Ferumi ID: %s", article_id)

        def background_task():
            try:
                video_path = main_orchestrator.process_video_payload(payload)

                if video_path and os.path.exists(video_path):
                    logger.info("  [Background] Video listo. Subiendo el MISMO archivo a R2, YouTube y Taisly (TikTok/IG/FB).")

                    nombre_video_r2 = f"video_short_{article_id}.mp4"
                    url_r2 = cloudflare_r2.upload_media_to_r2(video_path, nombre_video_r2)

                    youtube_id = youtube_uploader.upload_video(
                        file_path=video_path,
                        title=youtube_title,
                        description=youtube_desc,
                        tags=youtube_tags,
                    )

                    if youtube_id or url_r2:
                        if youtube_id:
                            youtube_uploader.mark_as_processed(article_id, youtube_id)
                        _notificar_webhook_node(
                            "video_complete", article_id, youtube_id=youtube_id, video_url=url_r2
                        )
                        try:
                            os.remove(video_path)
                            logger.info("  [Limpieza] Video borrado del disco: %s", video_path)
                            posible_jpg = video_path.rsplit(".", 1)[0] + ".jpg"
                            if os.path.exists(posible_jpg):
                                os.remove(posible_jpg)
                        except Exception as e:
                            logger.warning("  [Limpieza] No se pudo borrar el video: %s", e)
                    else:
                        logger.error("  [Background] Falló la subida a YouTube y Cloudflare.")
                        _notificar_webhook_node("video_failed", article_id, error="YouTube/Cloudflare Upload Failed")
                else:
                    logger.error("  [Background] El orquestador no devolvió un video válido.")
                    _notificar_webhook_node("video_failed", article_id, error="Video Generation Failed")

            except Exception as e:
                logger.error("  [Background] Error fatal: %s", e)
                _notificar_webhook_node("video_failed", article_id, error=str(e))
            finally:
                processing_lock.release()
                logger.info("  [API] [Lock Liberado] Servidor listo.")
                gc.collect()

        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()

        return jsonify({
            "message": "Tarea aceptada. Fabricando Short Ferumishop en segundo plano.",
            "status": "processing",
            "article_id": article_id,
        }), 202

    logger.warning("  [API] Servidor ocupado. Rechazando ID: %s", article_id)
    return jsonify({"error": "El servidor está procesando otro Short. Reintente en unos minutos."}), 503


def _notificar_webhook_node(endpoint, article_id, youtube_id=None, video_url=None, audio_url=None, error=None):
    webhook_url = f"{MAIN_API_URL}/api/articles/{endpoint}"
    headers = {"x-api-key": ADMIN_API_KEY}
    payload = {"articleId": article_id}
    if youtube_id:
        payload["youtubeId"] = youtube_id
    if video_url:
        payload["videoUrl"] = video_url
    if audio_url:
        payload["audioUrl"] = audio_url
    if error:
        payload["error"] = error
    try:
        r = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            logger.info("  [Webhook] API notificada (%s).", endpoint)
        else:
            logger.warning("  [Webhook] API respondió %s: %s", r.status_code, r.text)
    except Exception as e:
        logger.error("  [Webhook] Error de conexión: %s", e)


@app.route("/", methods=["GET"])
def index():
    return "<h1>Ferumishop — Motor de Shorts activo (1080p / 30fps)</h1>", 200


def background_audio_task(article_id, texto_completo):
    logger.info("  [Audio] Locución completa para %s", article_id)
    try:
        nombre_archivo = f"audio_{article_id}.mp3"
        os.makedirs("temp", exist_ok=True)
        ruta_audio = f"temp/{nombre_archivo}"
        texto_limpio = texto_completo.replace('"', "").replace("'", "")
        comando = f'edge-tts --voice "es-MX-DaliaNeural" --rate="+8%" --text "{texto_limpio}" --write-media {ruta_audio}'
        subprocess.run(comando, shell=True, check=True)
        url_r2 = cloudflare_r2.upload_media_to_r2(ruta_audio, nombre_archivo)
        if url_r2:
            _notificar_webhook_node("audio_complete", article_id, video_url=None, audio_url=url_r2)
        if os.path.exists(ruta_audio):
            os.remove(ruta_audio)
    except Exception as e:
        logger.error("  [Audio] Error generando MP3: %s", e)


@app.route("/api/tasks/audio", methods=["POST"])
def task_audio():
    data = request.json
    if request.headers.get("x-api-key") != ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    article_id = data.get("articleId")
    texto_completo = data.get("texto")
    if not article_id or not texto_completo:
        return jsonify({"error": "Faltan datos"}), 400
    thread = threading.Thread(target=background_audio_task, args=(article_id, texto_completo))
    thread.start()
    return jsonify({"message": "Generación de audio iniciada", "articleId": article_id}), 202


def run_cleanup_loop():
    import time
    time.sleep(10)
    while True:
        try:
            cloudflare_r2.delete_old_files_from_r2(days_old=28)
        except Exception as e:
            logger.error("  Error en limpieza R2: %s", e)
        time.sleep(86400)


cleanup_thread = threading.Thread(target=run_cleanup_loop, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
