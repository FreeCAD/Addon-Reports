# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
General purpose utilities.
"""

from __future__ import annotations

import functools
import threading


def thread_safe_cache(func):
    cache = {}
    locks = {}
    meta_lock = threading.Lock()  # protects the locks dict

    @functools.wraps(func)
    def wrapper(*args):
        with meta_lock:
            if args not in locks:
                locks[args] = threading.Lock()
            key_lock = locks[args]

        with key_lock:
            if args not in cache:
                cache[args] = func(*args)  # only ONE thread computes this
            return cache[args]

    wrapper.cache = cache
    return wrapper
