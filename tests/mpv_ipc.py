"""Общее для тестов: свойства плеера движка обоев через его IPC-канал."""
import json
import os

PIPE_DIR = '\\\\.\\pipe\\'


def pipes():
    """Каналы mpv движка Mimi Wallpapers (основной монитор — первым)."""
    names = [p for p in os.listdir(PIPE_DIR) if p.startswith('mimi-wallpaper-')]
    return sorted(names, key=lambda n: int(n.split('-')[3]))


def get(prop, idx=0):
    ps = pipes()
    if len(ps) <= idx:
        return None
    try:
        with open(PIPE_DIR + ps[idx], 'r+b', buffering=0) as p:
            p.write((json.dumps({'command': ['get_property', prop]}) + '\n').encode())
            line = p.readline()
            while b'"event"' in line:
                line = p.readline()
        return json.loads(line).get('data')
    except OSError:
        return None
