# -*- coding: utf-8 -*-
"""Motor seguro de FFmpeg para Shorts Ferumishop 1080x1920 @ 30fps."""

import os
import subprocess
import logging
from config import *

logger = logging.getLogger(__name__)


def execute_ffmpeg_command(cmd, timeout=300):
    """Ejecuta FFmpeg. Si falla, deja el stderr en el log para poder depurar."""
    try:
        logger.info("  [FFmpeg] Renderizando... (timeout %ss)", timeout)
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error("  [FFmpeg] TIMEOUT: el render superó %ss.", timeout)
        return False
    except subprocess.CalledProcessError as err:
        tail = (err.stderr or b"").decode("utf-8", errors="replace")[-1800:]
        logger.error("  [FFmpeg] FALLO de FFmpeg:\n%s", tail)
        return False
    except Exception as e:
        logger.error("  [FFmpeg] Error inesperado: %s", e)
        return False


def probe_wh(path):
    """Devuelve (width, height) o (None, None)."""
    if not path or not os.path.exists(path):
        return None, None
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        path,
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=15)
        parts = (result.stdout or "").strip().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return None, None


def probe_duration(path, default=4.0):
    if not path or not os.path.exists(path):
        return default
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=20)
        value = float((result.stdout or "").strip())
        if value > 0.05:
            return value
    except Exception:
        pass
    return default


def has_audio_stream(path):
    if not path or not os.path.exists(path):
        return False
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        path,
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=15)
        return "audio" in (result.stdout or "").lower()
    except Exception:
        return False


def encode_args():
    return [
        "-c:v", "libx264",
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.1",
        "-r", str(FPS),
        "-c:a", "aac",
        "-ar", str(AUDIO_RATE),
        "-ac", "2",
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
    ]
