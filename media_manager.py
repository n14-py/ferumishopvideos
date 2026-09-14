# -*- coding: utf-8 -*-
"""Gestor de branding y whoosh de transiciones (Ferumishop)."""

import os
import random
import logging
import shutil
from config import *

logger = logging.getLogger(__name__)


def get_random_file_from_dir(directory):
    if not os.path.exists(directory):
        logger.warning("  [Media] Directorio no encontrado: %s", directory)
        return None
    files = [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and not f.startswith(".")
    ]
    if not files:
        logger.warning("  [Media] Directorio vacío: %s", directory)
        return None
    return os.path.join(directory, random.choice(files))


def list_whoosh_files():
    if not os.path.exists(TRANSITIONS_DIR):
        return []
    files = [
        os.path.join(TRANSITIONS_DIR, f)
        for f in sorted(os.listdir(TRANSITIONS_DIR))
        if os.path.isfile(os.path.join(TRANSITIONS_DIR, f)) and not f.startswith(".")
    ]
    random.shuffle(files)
    return files


def get_random_whoosh():
    return get_random_file_from_dir(TRANSITIONS_DIR)


def get_random_sfx(sfx_type=None):
    """Ferumishop solo usa whoosh de transiciones. El resto se ignora."""
    return get_random_whoosh()


def get_random_bgm(mood=None):
    """Sin tensión/urgencia de noticias. Si más adelante hay BGM de tienda, se usa."""
    shop_dir = os.path.join(BGM_DIR, "shop")
    path = get_random_file_from_dir(shop_dir)
    if path:
        return path
    if mood:
        path = get_random_file_from_dir(os.path.join(BGM_DIR, mood))
        if path:
            return path
    return None


def get_logo_path():
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    if os.path.exists(LOGO_FALLBACK_PATH):
        return LOGO_FALLBACK_PATH
    return None


def copy_local_or_empty(src, dest):
    if not src or not os.path.exists(src):
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    return dest
