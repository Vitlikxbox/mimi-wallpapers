"""Автотест звука: режим «Звук везде» в настройках лаунчера (pywinauto + IPC плеера mpv)."""
import json
import os
import subprocess
import sys
import time

from pywinauto import Application, Desktop

EXE = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Mimi Wallpapers\MimiWallpapers.exe')
CFG = os.path.expandvars(r'%LOCALAPPDATA%\MimiWallpapers\config.json')
LS = os.path.expandvars(r'%LOCALAPPDATA%\Lively Wallpaper\Settings.json')
results = []


def check(name, ok, info=''):
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {info}' if info else ''), flush=True)


def mpv_volume():
    ps = ("$m=Get-CimInstance Win32_Process -Filter \"Name='mpv.exe'\" | Select-Object -First 1; "
          "$pipe=($m.CommandLine -replace '.*--input-ipc-server=(\\S+).*','$1'); "
          "$c=New-Object System.IO.Pipes.NamedPipeClientStream('.',$pipe,[System.IO.Pipes.PipeDirection]::InOut); $c.Connect(3000); "
          "$w=New-Object System.IO.StreamWriter($c); $r=New-Object System.IO.StreamReader($c); $w.AutoFlush=$true; "
          "$w.WriteLine('{\"command\":[\"get_property\",\"volume\"]}'); $l=$r.ReadLine(); "
          "while($l -notmatch '\"data\"|\"error\"'){$l=$r.ReadLine()}; $c.Close(); $l")
    out = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout
    try:
        return json.loads(out.strip().splitlines()[-1])['data']
    except Exception:
        return None


def set_mode(win, everywhere):
    win.set_focus()
    win.child_window(title_re='.*Настройки', control_type='Button').click_input()
    time.sleep(1.5)
    dlg = win.child_window(title='Настройки', control_type='Window')
    cb = dlg.child_window(title_re='Звук везде.*', control_type='CheckBox')
    if bool(cb.get_toggle_state()) != everywhere:
        cb.click_input()
    dlg.child_window(title='Сохранить', control_type='Button').click_input()
    time.sleep(16)                          # Lively перезапускается, обои и громкость возвращаются
    win.set_focus()
    time.sleep(3)


cfg = json.load(open(CFG, encoding='utf-8'))
check('звук в лаунчере включён', cfg.get('sound') is True, f"громкость {cfg.get('volume')}")
subprocess.run(['taskkill', '/f', '/im', 'MimiWallpapers.exe'], capture_output=True)
app = Application(backend='uia').start(EXE)
win = app.window(title='Mimi Wallpapers')
win.wait('visible', timeout=30)
time.sleep(3)

set_mode(win, True)
v = mpv_volume()
ls = json.load(open(LS, encoding='utf-8'))
check('«Звук везде»: Lively не глушит звук в окнах', ls.get('AudioOnlyOnDesktop') is False)
check('«Звук везде»: громкость есть при открытом окне', bool(v) and v > 0, f'громкость плеера {v}')

set_mode(win, False)
v = mpv_volume()
ls = json.load(open(LS, encoding='utf-8'))
check('по умолчанию: звук только на рабочем столе', ls.get('AudioOnlyOnDesktop') is True)
check('по умолчанию: при открытом окне тихо', v == 0, f'громкость плеера {v}')

win.close()
print('\nИТОГ:', sum(results), 'из', len(results))
sys.exit(0 if all(results) else 1)
