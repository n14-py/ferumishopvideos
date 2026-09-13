# -*- coding: utf-8 -*-
# ==============================================================================
# MÓDULO FFMPEG 01: ESCENA DE MAPA (VERSIÓN SHORTS 9:16)
# ==============================================================================
# Utiliza Mapbox para geocodificar. Aplica la estructura visual vertical (9:16)
# de fondo desenfocado + mapa nítido, con efecto de cámara lenta (dron).
# Soporta Banners Flotantes de Anuncios con animación de caída vertical.

import os
import logging
import requests
import subprocess
import textwrap
import urllib.parse
import uuid

from config import *

logger = logging.getLogger(__name__)

def obtener_duracion_audio(audio_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    try:
        resultado = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
        return float(resultado.stdout.strip()) + 0.4
    except Exception:
        return 25.0

MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "TU_CLAVE_MAPBOX_AQUI")

def obtener_imagen_mapa(ubicacion_texto, save_path):
    logger.info(f"  [FFmpeg 01 Mapa] Buscando coordenadas para: {ubicacion_texto}")
    try:
        query_codificada = urllib.parse.quote(ubicacion_texto)
        geo_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query_codificada}.json?access_token={MAPBOX_API_KEY}&limit=1"
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()
        
        if not geo_data.get('features'):
            logger.warning("  [FFmpeg 01 Mapa] No se encontró la ubicación. Usando mapa por defecto.")
            lon, lat = -57.4333, -25.3500 
        else:
            lon, lat = geo_data['features'][0]['center']
            
        mapa_url = f"https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/pin-s-marker+ff0000({lon},{lat})/{lon},{lat},13,0,0/1280x720?access_token={MAPBOX_API_KEY}"
        mapa_response = requests.get(mapa_url, stream=True, timeout=15)
        
        if mapa_response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in mapa_response.iter_content(8192):
                    f.write(chunk)
            return save_path
        else:
            logger.error(f"  [FFmpeg 01 Mapa] Error al descargar mapa: {mapa_response.status_code}")
            return None
    except Exception as e:
        logger.error(f"  [FFmpeg 01 Mapa] Error en API Mapbox: {e}")
        return None

def formatear_texto_mapa(texto, max_chars):
    if not texto:
        return ""
    texto = texto.replace("\\n", " ").replace("\n", " ").replace("\r", "")
    texto = " ".join(texto.split()) 
    texto = texto.replace("'", "\u2019").replace(":", "\\:") 
    
    wrapper = textwrap.TextWrapper(width=max_chars)
    word_list = wrapper.wrap(text=texto)
    
    # En Short permitimos 4 líneas para mapas
    if len(word_list) > 4:
        return "\n".join(word_list[:4]) + "..."
    return "\n".join(word_list)

def renderizar_escena_mapa(ubicacion_texto, overlay_mp4_path, audio_tts_path, bgm_path, sfx_path, texto_zocalo, output_path, unique_id, local_ad_banner=None):
    logger.info("  [FFmpeg 01 Mapa Short] Iniciando renderizado de la escena...")
    
    mapa_img_path = os.path.join(TEMP_IMG_DIR, f"mapa_{unique_id}.jpg")
    if not obtener_imagen_mapa(ubicacion_texto, mapa_img_path):
        return False
        
    filename = os.path.basename(overlay_mp4_path)
    config = get_layout_config(filename) if 'get_layout_config' in globals() else LAYOUT_CONFIG.get(filename, DEFAULT_LAYOUT)
    
    clean_text = formatear_texto_mapa(texto_zocalo, config["max_letras_por_linea"])
    x, y = config["texto_x"], config["texto_y"]
    color, size = config["color"], config["font_size"]
    shadow = "bordercolor=black:borderw=2"
    
    texto_path = os.path.join(TEMP_VIDEO_DIR, f"txt_map_{uuid.uuid4().hex[:6]}.txt").replace('\\', '/')
    
    if clean_text:
        with open(texto_path, "wb") as f:
            f.write(clean_text.encode("utf-8"))
            
    # TUBERÍA VISUAL SHORTS: Blur -> Centrado -> Zoompan a todo el bloque -> Presentador Verde
    filter_complex = (
        f"[0:v]scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=increase,"
        f"crop={RESOLUTION_W}:{RESOLUTION_H}:(iw-ow)/2:(ih-oh)/2,boxblur=20:5[bg_blur];"
        f"[0:v]scale={RESOLUTION_W}:-1[img_sharp];"
        f"[bg_blur][img_sharp]overlay=0:(H-h)/2[combined];"
        f"[combined]zoompan=z='min(zoom+0.002,1.2)':d=450:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={RESOLUTION_W}x{RESOLUTION_H}:fps={FPS}[bg];"
        f"[1:v]scale={RESOLUTION_W}:{RESOLUTION_H}[v_scaled];"
        f"[v_scaled]chromakey={CHROMA_COLOR}:{CHROMA_SIMILARITY}:{CHROMA_BLEND}[v_keyed];"
        f"[bg][v_keyed]overlay=0:0:shortest=1[comp];"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", mapa_img_path,         
        "-stream_loop", "-1", "-i", overlay_mp4_path
    ]
    
    # --- ENTRADA EXTRA: BANNER PUBLICITARIO ---
    banner_idx = -1
    audio_idx = 2
    
    if local_ad_banner and os.path.exists(local_ad_banner):
        if local_ad_banner.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            cmd.extend(["-loop", "1", "-framerate", str(FPS), "-i", local_ad_banner])
        else:
            cmd.extend(["-stream_loop", "-1", "-i", local_ad_banner])
            
        banner_idx = 2
        audio_idx = 3 # Desplazamos el audio
        logger.info("  [FFmpeg 01 Mapa] Inyectando Banner Flotante de Anuncio.")
        
    # --- ENTRADA AUDIO TTS ---
    cmd.extend(["-i", audio_tts_path])
    
    nodo_actual = "comp"
    
# --- INYECCIÓN DEL BANNER FLOTANTE (ANIMACIÓN VERTICAL SHORTS) ---
    if banner_idx != -1:
        # scale={RESOLUTION_W - 80} achica 40px por lado. x='(W-w)/2' lo centra. y=30 lo pega casi al techo.
        filter_complex += (
            f"[{banner_idx}:v]scale={RESOLUTION_W - 80}:-2,setsar=1[banner_scaled];"
            f"[{nodo_actual}][banner_scaled]overlay=x='(W-w)/2':y='if(lte(t,1),-h+(h+30)*t,30)'[comp_ad];"
        )
        nodo_actual = "comp_ad"

    if clean_text:
        font_safe = str(FONT_PATH).replace('\\', '/').replace(':', '\\:')
        txt_safe = str(texto_path).replace('\\', '/').replace(':', '\\:')
        filter_complex += f"[{nodo_actual}]drawtext=fontfile='{font_safe}':textfile='{txt_safe}':fontcolor={color}:fontsize={size}:{shadow}:x={x}:y={y}[vout];"
    else:
        filter_complex += f"[{nodo_actual}]copy[vout];"
        
    audio_inputs = f"[{audio_idx}:a]"
    input_count = 1
    current_in_idx = audio_idx + 1
    
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-i", bgm_path])              
        audio_inputs += f"[{current_in_idx}:a]"
        current_in_idx += 1
        input_count += 1
        
    if sfx_path and os.path.exists(sfx_path):
        cmd.extend(["-i", sfx_path])              
        audio_inputs += f"[{current_in_idx}:a]"
        current_in_idx += 1
        input_count += 1
        
    if input_count > 1:
        filter_complex += f"{audio_inputs}amix=inputs={input_count}:duration=first:dropout_transition=2:weights=1 0.1 0.2[aout]"
        audio_map = "-map [aout]"
    else:
        filter_complex = filter_complex.rstrip(';')
        audio_map = f"-map {audio_idx}:a"
        
    duracion_exacta = obtener_duracion_audio(audio_tts_path)
    
    cmd.extend([
        "-filter_threads", "2",
        "-filter_complex", filter_complex,
        "-map", "[vout]", 
        *audio_map.split(),
        "-c:v", "libx264", "-preset", "superfast", "-threads", "2", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-t", str(duracion_exacta), output_path
    ])
    
    try:
        proceso = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proceso.communicate(timeout=200)
        
        return proceso.returncode == 0 and os.path.exists(output_path)
        
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.communicate()
        return False
    except Exception as e:
        if 'proceso' in locals():
            proceso.kill()
            proceso.communicate()
        return False
        
    finally:
        # Lógica estricta de borrado
        if 'texto_path' in locals() and os.path.exists(texto_path):
            try: os.remove(texto_path)
            except: pass
        if 'mapa_img_path' in locals() and os.path.exists(mapa_img_path):
            try: os.remove(mapa_img_path)
            except: pass