"""Автотест звука: режим «Звук везде» в настройках лаунчера (pywinauto + IPC плеера движка)."""
import json
import os
import subprocess
import sys
import time

from pywinauto import Application

import mpv_ipc

EXE = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Mimi Wallpapers\MimiWallpapers.exe')
CFG = os.path.expandvars(r'%LOCALAPPDATA%\MimiWallpapers\config.json')
results = []


def check(name, ok, info=''):
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {info}' if info else ''), flush=True)


def set_mode(win, everywhere):
    win.set_focus()
    win.child_window(title_re='.*Настройки', control_type='Button').click_input()
    time.sleep(1.5)
    dlg = win.child_window(title='Настройки', control_type='Window')
    cb = dlg.child_window(title_re='Звук везде.*', control_type='CheckBox')
    if bool(cb.get_toggle_state()) != everywhere:
        cb.click_input()
    dlg.child_window(title='Сохранить', control_type='Button').click_input()
    win.set_focus()
    time.sleep(2)                           # движок замечает новый config.json за полсекунды


cfg = json.load(open(CFG, encoding='utf-8-sig'))
check('звук в лаунчере включён', cfg.get('sound') is True, f"громкость {cfg.get('volume')}")
# закрываем только окно лаунчера: у движка то же имя процесса, его не трогаем
subprocess.run(['taskkill', '/f', '/fi', 'IMAGENAME eq MimiWallpapers.exe', '/fi', 'WINDOWTITLE eq Mimi Wallpapers'],
               capture_output=True)
app = Application(backend='uia').start(EXE)
win = app.window(title='Mimi Wallpapers')
win.wait('visible', timeout=30)
time.sleep(4)
check('движок обоев работает', bool(mpv_ipc.pipes()), ', '.join(mpv_ipc.pipes()))

set_mode(win, True)
check('«Звук везде»: при открытом окне звук есть', mpv_ipc.get('mute') is False, f"mute={mpv_ipc.get('mute')}")
check('громкость плеера = громкость из настроек', mpv_ipc.get('volume') == cfg.get('volume'),
      f"{mpv_ipc.get('volume')} / {cfg.get('volume')}")

set_mode(win, False)
check('по умолчанию: при открытом окне тихо', mpv_ipc.get('mute') is True, f"mute={mpv_ipc.get('mute')}")

win.close()
print('\nИТОГ:', sum(results), 'из', len(results))
sys.exit(0 if all(results) else 1)
