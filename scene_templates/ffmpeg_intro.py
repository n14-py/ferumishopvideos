# -*- coding: utf-8 -*-
# ==============================================================================
# MÓDULO FFMPEG: ENSAMBLADOR DE INTROS (VERSIÓN SHORTS)
# ==============================================================================
# Se encarga exclusivamente de las intros verticales. NO HAY CHROMA KEY.
# Es video directo + texto gigante centrado + audio mezclado.

import os
import logging
import subprocess
import textwrap
import uuid

from config import *

logger = logging.getLogger(__name__)

def formatear_texto_intro(texto, max_chars):
    """Corta el titular para que encaje perfecto y se vea gigante en el Short."""
    if not texto:
        return ""
    # Escapar comillas y limpiar saltos raros
    texto = texto.replace("\\n", " ").replace("\n", " ")
    texto = " ".join(texto.split())
    texto = texto.replace("'", "\u2019").replace(":", "\:")
    
    wrapper = textwrap.TextWrapper(width=max_chars)
    word_list = wrapper.wrap(text=texto)
    
    if len(word_list) > 3:
        return "\n".join(word_list[:3]) + "..."
    return "\n".join(word_list)

# AQUÍ ESTÁ LA CORRECCIÓN: Agregamos local_ad_banner=None al final de los parámetros
def ensamblar_intro(intro_path, audio_tts_path, bgm_path, sfx_path, texto, output_path, local_ad_banner=None):
    """
    Toma el video de intro base vertical y le incrusta el título, la voz y la música.
    Nota: Se ignora intencionalmente el banner en la Intro para no arruinar el gancho.
    """
    logger.info(f"  [FFmpeg Intro Short] Ensamblando escena de Introducción...")
    logger.info(f"  --> Intro Base: {os.path.basename(intro_path)}")
    
    if not os.path.exists(intro_path) or not os.path.exists(audio_tts_path):
        logger.error("  [FFmpeg Intro Short] Faltan archivos clave (Intro o Audio) para ensamblar.")
        return False

    filename = os.path.basename(intro_path)
    config = get_layout_config(filename) if 'get_layout_config' in globals() else LAYOUT_CONFIG.get(filename, DEFAULT_LAYOUT)
    
    clean_text = formatear_texto_intro(texto, config["max_letras_por_linea"])
    
    x, y = config["texto_x"], config["texto_y"]
    color, size = config["color"], config["font_size"]
    shadow = "shadowcolor=black@0.8:shadowx=0:shadowy=0"
    
    texto_path = os.path.join(TEMP_VIDEO_DIR, f"txt_intro_{uuid.uuid4().hex[:6]}.txt").replace('\\', '/')
    if clean_text:
        with open(texto_path, "wb") as f:
            f.write(clean_text.encode("utf-8"))

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", intro_path,
        "-i", audio_tts_path
    ]
    
    # Fuerza el formato 1080x1920 por si la intro original es un poco distinta
    filter_complex = (
        f"[0:v]scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=increase,"
        f"crop={RESOLUTION_W}:{RESOLUTION_H}:(iw-ow)/2:(ih-oh)/2[bg];"
    )
    
    if clean_text:
        font_safe = str(FONT_PATH).replace('\\', '/').replace(':', '\\:')
        txt_safe = str(texto_path).replace('\\', '/').replace(':', '\\:')
        filter_complex += f"[bg]drawtext=fontfile='{font_safe}':textfile='{txt_safe}':fontcolor={color}:fontsize={size}:{shadow}:x={x}:y={y}[vout];"
    else:
        filter_complex += f"[bg]copy[vout];"
        
    audio_inputs = "[1:a]"
    input_count = 1
    
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-i", bgm_path])
        audio_inputs += "[2:a]"
        input_count += 1
        
    if sfx_path and os.path.exists(sfx_path):
        cmd.extend(["-i", sfx_path])
        audio_inputs += "[3:a]"
        input_count += 1
        
    if input_count > 1:
        filter_complex += f"{audio_inputs}amix=inputs={input_count}:duration=first:dropout_transition=2:weights=1 0.15 0.3[aout]"
        audio_map = "-map [aout]"
    else:
        filter_complex = filter_complex.rstrip(';')
        audio_map = "-map 1:a"
        
    cmd.extend([
        "-filter_threads", "2",
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        *audio_map.split(),
        "-c:v", "libx264",
        "-preset", VIDEO_PRESET,
        "-threads", "2",
        "-r", str(FPS),
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        output_path
    ])
    
    try:
        proceso = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proceso.communicate(timeout=200)
        
        if proceso.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            logger.info("  [FFmpeg Intro Short] ¡ÉXITO! Intro renderizada.")
            return True
        else:
            logger.error("  [FFmpeg Intro Short] El archivo resultante está vacío o falló.")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("  [FFmpeg Intro Short] TIMEOUT Zombi...")
        proceso.kill()
        proceso.communicate()
        return False
    except Exception as e:
        if 'proceso' in locals():
            proceso.kill()
            proceso.communicate()
        logger.error(f"  [FFmpeg Intro Short] Error crítico: {e}")
        return False
        
    finally:
        if 'texto_path' in locals() and os.path.exists(texto_path):
            try: os.remove(texto_path)
            except: pass