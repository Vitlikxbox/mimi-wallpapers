"""Автотест движка обоев (launcher/engine.py) на установленной программе.

Проверяет: встраивание под ярлыки рабочего стола, один экземпляр, смену ролика без перезапуска плеера,
паузу при полноэкранном окне, звук по настройкам, закрытие плеера вместе с движком.
Настройки пользователя (config.json) в конце возвращаются как были.
"""
import ctypes
import json
import os
import subprocess
import sys
import time

import mpv_ipc

EXE = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Mimi Wallpapers\MimiWallpapers.exe')
DATA = os.path.expandvars(r'%LOCALAPPDATA%\MimiWallpapers')
CFG = os.path.join(DATA, 'config.json')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MIMI_DEV=1 — проверять движок из исходников, а не установленную программу
ENGINE = ([os.path.join(ROOT, '.venv', 'Scripts', 'pythonw.exe'), os.path.join(ROOT, 'launcher', 'engine.py')]
          if os.environ.get('MIMI_DEV') else [EXE, '--engine'])
results = []
u32 = ctypes.windll.user32
u32.GetParent.restype = ctypes.c_void_p
u32.FindWindowW.restype = ctypes.c_void_p
u32.FindWindowExW.restype = ctypes.c_void_p


def check(name, ok, info=''):
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {info}' if info else ''), flush=True)


def procs(name):
    out = subprocess.run(['tasklist', '/fi', f'IMAGENAME eq {name}', '/fo', 'csv', '/nh'], capture_output=True,
                         text=True).stdout
    return [line for line in out.splitlines() if name.lower() in line.lower()]


def set_cfg(**kw):
    c = json.load(open(CFG, encoding='utf-8-sig'))
    c.update(kw)
    tmp = CFG + '.tmp'
    json.dump(c, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    os.replace(tmp, CFG)


def wait(cond, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.3)
    return False


def mpv_hwnd():
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    progman = u32.FindWindowW('Progman', None)

    def cb(h, _):
        b = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(ctypes.c_void_p(h), b, 64)
        if b.value == 'mpv':
            found.append(h)
        return True
    u32.EnumChildWindows(ctypes.c_void_p(progman), proc(cb), 0)
    return found, progman


def cls_of(h):
    b = ctypes.create_unicode_buffer(64)
    u32.GetClassNameW(ctypes.c_void_p(h), b, 64)
    return b.value


def desktop_order():
    """Классы дочерних окон Progman сверху вниз (только значимые)."""
    progman = u32.FindWindowW('Progman', None)
    out, c = [], u32.FindWindowExW(ctypes.c_void_p(progman), None, None, None)
    while c:
        if cls_of(c) in ('SHELLDLL_DefView', 'MimiWallpaperHost', 'WorkerW'):
            out.append(cls_of(c))
        c = u32.FindWindowExW(ctypes.c_void_p(progman), ctypes.c_void_p(c), None, None)
    return out


def order_ok():
    """Ярлыки выше видео, видео выше любого слоя WorkerW."""
    o = desktop_order()
    if 'MimiWallpaperHost' not in o or 'SHELLDLL_DefView' not in o:
        return False
    i = o.index('MimiWallpaperHost')
    return o.index('SHELLDLL_DefView') < i and 'WorkerW' not in o[:i]


def top_level_mpv():
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    u32.EnumWindows(proc(lambda h, _: found.append(h) if cls_of(h) == 'mpv' else None or True), 0)
    return found


backup = open(CFG, encoding='utf-8-sig').read()
orig = json.loads(backup)
videos = [f[:-4] for f in os.listdir(os.path.join(DATA, 'videos')) if f.endswith('.mkv')]
first = orig.get('current') or videos[0]
other = next(v for v in videos if v != first)
try:
    # 1. запуск
    subprocess.run(['taskkill', '/f', '/im', 'MimiWallpapers.exe'], capture_output=True)
    subprocess.run(['taskkill', '/f', '/im', 'pythonw.exe'], capture_output=True)
    time.sleep(1.5)
    check('после остановки движка плеер закрылся', not procs('mpv.exe'))
    set_cfg(current=first, sound=True, audio_everywhere=False)
    subprocess.Popen(ENGINE)
    check('движок запустил плеер', wait(lambda: mpv_ipc.get('path') is not None, 15))
    wait(lambda: bool(mpv_hwnd()[0]), 10)
    hs, progman = mpv_hwnd()
    check('видео встроено в рабочий стол под ярлыки', bool(hs), f'окон mpv внутри Progman: {len(hs)}')
    hw = None
    wait(lambda: mpv_ipc.get('hwdec-current') not in (None, ''), 5)
    hw = mpv_ipc.get('hwdec-current')
    check('аппаратное декодирование', bool(hw) and hw != 'no', str(hw))
    t1 = mpv_ipc.get('time-pos') or 0
    check('видео идёт', wait(lambda: (mpv_ipc.get('time-pos') or 0) > t1 + 0.5 and mpv_ipc.get('pause') is False, 8),
          f"pause={mpv_ipc.get('pause')} time={mpv_ipc.get('time-pos')}")
    check('бесконечный повтор', mpv_ipc.get('loop-file') == 'inf')
    check('у плеера нет окна на панели задач (нечего случайно закрыть)', not top_level_mpv())
    check('порядок: ярлыки › видео › фон WorkerW', order_ok(), ' › '.join(desktop_order()))
    subprocess.run(['taskkill', '/f', '/im', 'mpv.exe'], capture_output=True)   # плеер «вылетел»
    check('плеер вылетел → движок запустил его снова', wait(lambda: mpv_ipc.get('path') is not None and bool(procs('mpv.exe')), 10))
    check('после вылета видео снова под ярлыками', wait(order_ok, 5),
          ' › '.join(desktop_order()))

    # 2. один экземпляр
    subprocess.Popen(ENGINE)
    time.sleep(3)
    check('второй запуск не создаёт копию', len(procs('mpv.exe')) == 1, f'mpv: {len(procs("mpv.exe"))}')

    # 3. смена ролика
    pid_before = mpv_ipc.pipes()
    set_cfg(current=other)
    check('ролик сменился', wait(lambda: other in (mpv_ipc.get('path') or ''), 10), str(mpv_ipc.get('path')))
    check('без перезапуска плеера (без мелькания)', mpv_ipc.pipes() == pid_before)

    # 4. звук
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtCore import Qt
    from pywinauto import Application as PwaApp
    app = QApplication.instance() or QApplication(sys.argv)
    normal = QWidget()
    normal.setWindowTitle('Mimi test window')
    normal.resize(400, 300)
    normal.show()
    app.processEvents()
    PwaApp(backend='win32').connect(handle=int(normal.winId())).window(handle=int(normal.winId())).set_focus()
    check('звук только на рабочем столе: при активном окне тихо', wait(lambda: mpv_ipc.get('mute') is True, 4))
    set_cfg(audio_everywhere=True)
    check('«звук везде»: звук есть', wait(lambda: mpv_ipc.get('mute') is False, 5))
    set_cfg(sound=False)
    check('звук выключен', wait(lambda: mpv_ipc.get('mute') is True, 5))
    set_cfg(sound=True, audio_everywhere=False)
    normal.close()

    # 5. полноэкранное окно → пауза
    full = QWidget()
    full.setWindowFlag(Qt.FramelessWindowHint)
    full.setStyleSheet('background:#201020')
    full.showFullScreen()
    app.processEvents()
    PwaApp(backend='win32').connect(handle=int(full.winId())).window(handle=int(full.winId())).set_focus()
    end = time.time() + 6
    paused = False
    while time.time() < end and not paused:
        app.processEvents()
        time.sleep(0.2)
        paused = mpv_ipc.get('pause') is True
    check('полноэкранное окно (игра) → обои на паузе', paused)
    full.close()
    app.processEvents()
    check('окно закрыли → обои снова идут', wait(lambda: mpv_ipc.get('pause') is False, 6))

    # 6. выключение обоев
    set_cfg(current=None)
    check('обои выключены → движок и плеер закрылись', wait(lambda: not procs('mpv.exe'), 8))
finally:
    open(CFG, 'w', encoding='utf-8').write(backup)
    if orig.get('current'):
        subprocess.Popen(ENGINE)

print('\nИТОГ:', sum(results), 'из', len(results))
sys.exit(0 if all(results) else 1)
