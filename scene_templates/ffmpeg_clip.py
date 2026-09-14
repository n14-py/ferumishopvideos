# -*- coding: utf-8 -*-
"""
Ensamblador de clips Ferumishop.
Video tras video, 1080x1920 @ 30fps, sin plantillas de noticias.

Capa visual de cada clip:
  1. Producto (video o foto) llenando 9:16
  2. Texto en pantalla ARRIBA al centro (lo envía la IA)
  3. Logo Ferumi al medio, un poco abajo, semitransparente
  4. Número de WhatsApp debajo del logo (lo envía la IA)
  5. Whoosh + transiciones xfade entre clips
"""

import os
import random
import logging
import textwrap
import uuid

from config import *
from ffmpeg_core import execute_ffmpeg_command, probe_duration, encode_args, probe_wh

logger = logging.getLogger(__name__)


def _ffmpeg_path(path):
    return str(path).replace("\\", "/").replace(":", "\\:")


def _write_text_file(text, prefix):
    path = os.path.join(TEMP_VIDEO_DIR, f"{prefix}_{uuid.uuid4().hex[:8]}.txt")
    with open(path, "wb") as f:
        f.write((text or "").encode("utf-8"))
    return path


def formatear_texto_pantalla(texto, max_chars=TOP_TEXT_MAX_CHARS, max_lines=TOP_TEXT_MAX_LINES):
    if not texto:
        return ""
    texto = str(texto).replace("\\n", " ").replace("\n", " ").replace("\r", " ")
    texto = " ".join(texto.split())
    wrapper = textwrap.TextWrapper(width=max_chars)
    lines = wrapper.wrap(text=texto)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(".…") + "…"
    return "\n".join(lines)


def formatear_whatsapp(numero):
    digits = "".join(ch for ch in str(numero or "") if ch.isdigit())
    if not digits:
        digits = "".join(ch for ch in DEFAULT_WHATSAPP if ch.isdigit())
    local = digits
    if local.startswith("595") and len(local) >= 12:
        rest = local[3:]
        if rest.startswith("9") and len(rest) == 9:
            local = f"0{rest[0:3]} {rest[3:6]} {rest[6:]}"
        else:
            local = rest
    elif len(local) == 10 and local.startswith("09"):
        local = f"{local[0:4]} {local[4:7]} {local[7:]}"
    return f"WhatsApp  {local}"


def _logo_file():
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    if os.path.exists(LOGO_FALLBACK_PATH):
        return LOGO_FALLBACK_PATH
    return None


def _logo_draw_height():
    logo = _logo_file()
    w, h = probe_wh(logo) if logo else (None, None)
    if w and h and w > 0:
        return max(80, int(LOGO_WIDTH * (h / float(w))))
    return int(LOGO_WIDTH * 0.5)


def _build_visual_filter(es_video, has_text, has_logo):
    logo_h = _logo_draw_height()
    logo_y = f"(H-h)/2+{LOGO_Y_OFFSET}"
    wa_y = int((RESOLUTION_H - logo_h) / 2 + LOGO_Y_OFFSET + logo_h + 28)
    font_safe = _ffmpeg_path(FONT_PATH)

    if es_video:
        fondo = (
            f"[0:v]format=yuv420p,fps={FPS},"
            f"scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=increase,"
            f"crop={RESOLUTION_W}:{RESOLUTION_H}:(iw-ow)/2:(ih-oh)/2,"
            f"eq=contrast=1.06:saturation=1.12:brightness=0.01,"
            f"setsar=1[bg];"
        )
    else:
        zoom_w = int(RESOLUTION_W * 1.25)
        zoom_h = int(RESOLUTION_H * 1.25)
        fondo = (
            f"[0:v]scale={zoom_w}:{zoom_h}:force_original_aspect_ratio=increase,"
            f"crop={zoom_w}:{zoom_h},"
            f"zoompan=z='min(1.0+0.00045*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={RESOLUTION_W}x{RESOLUTION_H}:fps={FPS},"
            f"eq=contrast=1.05:saturation=1.1,setsar=1,format=yuv420p[bg];"
        )

    if has_logo:
        overlay = (
            f"[1:v]scale={LOGO_WIDTH}:-1,format=rgba,split=3[lg][sh][wh];"
            f"[sh]colorchannelmixer=rr=0:gg=0:bb=0:aa=0.28,boxblur=8:2[shadow];"
            f"[wh]eq=saturation=0:brightness=0.9,colorchannelmixer=aa=0.22[halo];"
            f"[lg]colorchannelmixer=aa={LOGO_OPACITY}[mark];"
            f"[bg][shadow]overlay=x=(W-w)/2+5:y=(H-h)/2+{LOGO_Y_OFFSET}+5[bg_sh];"
            f"[bg_sh][halo]overlay=x=(W-w)/2:y=(H-h)/2+{LOGO_Y_OFFSET}[bg_halo];"
            f"[bg_halo][mark]overlay=x=(W-w)/2:y=(H-h)/2+{LOGO_Y_OFFSET}[branded];"
        )
        text_src = "branded"
    else:
        overlay = "[bg]copy[branded];"
        text_src = "branded"

    if has_text:
        text_filter = (
            f"[{text_src}]drawtext=fontfile='{font_safe}':textfile='{{txt}}':"
            f"fontcolor={TOP_TEXT_COLOR}:fontsize={TOP_TEXT_SIZE}:"
            f"borderw=5:bordercolor=black:line_spacing=10:"
            f"x=(w-text_w)/2:y={TOP_TEXT_Y}[with_text];"
        )
    else:
        text_filter = f"[{text_src}]copy[with_text];"

    wa_filter = (
        f"[with_text]drawtext=fontfile='{font_safe}':textfile='{{wa}}':"
        f"fontcolor={WHATSAPP_COLOR}:fontsize={WHATSAPP_FONT_SIZE}:"
        f"borderw=3:bordercolor=black:"
        f"x=(w-text_w)/2:y={wa_y}[vout]"
    )
    return fondo + overlay + text_filter + wa_filter


def renderizar_clip(fondo_path, audio_tts_path, texto_pantalla, whatsapp_text, sfx_path, output_path, duracion=None):
    """Renderiza UN clip de producto con branding Ferumi."""
    if not fondo_path or not os.path.exists(fondo_path):
        logger.error("  [Clip] Falta el video/foto de fondo.")
        return False

    es_video = fondo_path.lower().endswith((".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v"))
    if duracion is None:
        if audio_tts_path and os.path.exists(audio_tts_path):
            duracion = probe_duration(audio_tts_path, 4.0) + 0.25
        else:
            duracion = min(probe_duration(fondo_path, 5.0), 8.0)
    duracion = max(float(duracion), 1.3)

    clean_text = formatear_texto_pantalla(texto_pantalla)
    wa_line = formatear_whatsapp(whatsapp_text)
    txt_path = _write_text_file(clean_text, "txt")
    wa_path = _write_text_file(wa_line, "wa")
    logo = _logo_file()

    filtro = _build_visual_filter(es_video, bool(clean_text), bool(logo))
    filtro = filtro.replace("{txt}", _ffmpeg_path(txt_path)).replace("{wa}", _ffmpeg_path(wa_path))

    cmd = ["ffmpeg", "-y"]
    next_idx = 0

    if es_video:
        cmd.extend(["-stream_loop", "-1", "-i", fondo_path])
    else:
        cmd.extend(["-loop", "1", "-framerate", str(FPS), "-i", fondo_path])
    next_idx = 1

    if logo:
        cmd.extend(["-loop", "1", "-framerate", str(FPS), "-i", logo])
        next_idx += 1

    audio_indices = []
    if audio_tts_path and os.path.exists(audio_tts_path):
        cmd.extend(["-i", audio_tts_path])
        audio_indices.append(next_idx)
        next_idx += 1
    if sfx_path and os.path.exists(sfx_path):
        cmd.extend(["-i", sfx_path])
        audio_indices.append(next_idx)
        next_idx += 1
    if not audio_indices:
        cmd.extend(["-f", "lavfi", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo"])
        audio_indices.append(next_idx)

    if len(audio_indices) == 1:
        filtro += (
            f";[{audio_indices[0]}:a]aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"aresample={AUDIO_RATE},volume=1.0[aout]"
        )
    else:
        mix = "".join(f"[{i}:a]" for i in audio_indices)
        filtro += (
            f";{mix}amix=inputs={len(audio_indices)}:duration=first:dropout_transition=2:"
            f"weights=1 0.55[amixed];"
            f"[amixed]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample={AUDIO_RATE}[aout]"
        )

    cmd.extend([
        "-filter_complex", filtro,
        "-map", "[vout]",
        "-map", "[aout]",
        *encode_args(),
        "-t", f"{duracion:.3f}",
        output_path,
    ])

    try:
        ok = execute_ffmpeg_command(cmd, timeout=420)
        return ok and os.path.exists(output_path) and os.path.getsize(output_path) > 1024
    finally:
        for tmp in (txt_path, wa_path):
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass


def concatenar_con_transiciones(clips, output_path, whoosh_paths=None):
    """Pega clips con xfade + whoosh en cada corte. Si xfade falla, concat duro."""
    clips = [c for c in clips if c and os.path.exists(c)]
    if not clips:
        return False
    if len(clips) == 1:
        cmd = ["ffmpeg", "-y", "-i", clips[0], "-c", "copy", output_path]
        if execute_ffmpeg_command(cmd, timeout=60) and os.path.exists(output_path):
            return True
        cmd = ["ffmpeg", "-y", "-i", clips[0], *encode_args(), output_path]
        return execute_ffmpeg_command(cmd, timeout=180) and os.path.exists(output_path)

    durations = [probe_duration(c, 4.0) for c in clips]
    td = min(TRANSITION_DURATION, min(durations) * 0.35)
    td = max(0.22, td)

    cmd = ["ffmpeg", "-y"]
    for clip in clips:
        cmd.extend(["-i", clip])

    whoosh_paths = [w for w in (whoosh_paths or []) if w and os.path.exists(w)]
    whoosh_start_idx = len(clips)
    n_whoosh = max(0, len(clips) - 1)
    chosen_whoosh = []
    for i in range(n_whoosh):
        src = whoosh_paths[i % len(whoosh_paths)] if whoosh_paths else None
        chosen_whoosh.append(src)
        if src:
            cmd.extend(["-i", src])

    vchain = ""
    last_v = "0:v"
    last_a = "0:a"
    offset = 0.0
    whoosh_delays = []

    for i in range(1, len(clips)):
        offset += durations[i - 1] - td
        whoosh_delays.append(max(0.0, offset))
        trans = random.choice(XFADE_TRANSITIONS)
        v_out = f"vx{i}"
        a_out = f"ax{i}"
        vchain += (
            f"[{last_v}][{i}:v]xfade=transition={trans}:duration={td:.3f}:offset={offset:.3f}[{v_out}];"
            f"[{last_a}][{i}:a]acrossfade=d={td:.3f}[{a_out}];"
        )
        last_v, last_a = v_out, a_out

    vchain += f"[{last_v}]fps={FPS},format=yuv420p,setsar=1[outv];"

    mix_parts = [f"[{last_a}]"]
    mix_count = 1
    wi = whoosh_start_idx
    for delay, src in zip(whoosh_delays, chosen_whoosh):
        if not src:
            continue
        delay_ms = int(delay * 1000)
        vchain += (
            f"[{wi}:a]aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"volume=0.72,adelay={delay_ms}|{delay_ms}[wh{wi}];"
        )
        mix_parts.append(f"[wh{wi}]")
        mix_count += 1
        wi += 1

    if mix_count == 1:
        vchain += f"{mix_parts[0]}aformat=sample_fmts=fltp:channel_layouts=stereo,aresample={AUDIO_RATE}[outa]"
    else:
        weights = "1 " + " ".join(["0.65"] * (mix_count - 1))
        vchain += (
            f"{''.join(mix_parts)}amix=inputs={mix_count}:duration=first:dropout_transition=2:weights={weights}[amix];"
            f"[amix]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample={AUDIO_RATE}[outa]"
        )

    cmd.extend([
        "-filter_complex", vchain,
        "-map", "[outv]",
        "-map", "[outa]",
        *encode_args(),
        output_path,
    ])

    logger.info("  [Transiciones] Ensamblando %s clips con xfade + whoosh...", len(clips))
    if execute_ffmpeg_command(cmd, timeout=600) and os.path.exists(output_path) and os.path.getsize(output_path) > 2048:
        return True

    logger.warning("  [Transiciones] xfade falló. Concatenación dura de respaldo.")
    return concatenar_duro(clips, output_path)


def concatenar_duro(clips, output_path):
    cmd = ["ffmpeg", "-y"]
    filter_complex = ""
    concat_inputs = ""
    for i, escena in enumerate(clips):
        cmd.extend(["-i", escena])
        filter_complex += (
            f"[{i}:v]scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=decrease,"
            f"pad={RESOLUTION_W}:{RESOLUTION_H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p[v{i}];"
            f"[{i}:a]aresample={AUDIO_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}];"
        )
        concat_inputs += f"[v{i}][a{i}]"
    filter_complex += f"{concat_inputs}concat=n={len(clips)}:v=1:a=1[outv][outa]"
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        *encode_args(),
        output_path,
    ])
    return execute_ffmpeg_command(cmd, timeout=600) and os.path.exists(output_path)
