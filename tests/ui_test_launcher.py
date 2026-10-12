"""Автотест лаунчера Mimi Wallpapers через UI Automation (pywinauto): нажимает настоящие кнопки и проверяет результат."""
import os
import subprocess
import sys
import time

from pywinauto import Application, Desktop

EXE = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Mimi Wallpapers\MimiWallpapers.exe')
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots')
os.makedirs(SHOTS, exist_ok=True)
results = []


def check(name, ok, info=''):
    results.append((name, ok, info))
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {info}' if info else ''), flush=True)


def shot(name):
    from PIL import ImageGrab
    ImageGrab.grab().save(os.path.join(SHOTS, name + '.png'))


def texts(win):
    out = []
    for c in win.descendants():
        try:
            t = c.window_text()
            if t:
                out.append(t)
        except Exception:
            pass
    return out


def dialog(title_re, timeout=10):
    """Диалог Qt: ищем и как дочернее окно лаунчера, и как отдельное окно."""
    end = time.time() + timeout
    while time.time() < end:
        for spec in (win.child_window(title_re=title_re, control_type='Window'),
                     Desktop(backend='uia').window(title_re=title_re)):
            try:
                if spec.exists(timeout=0.5):
                    return spec
            except Exception:
                pass
        time.sleep(0.3)
    return None


def wait_text(win, needle, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        hit = [t for t in texts(win) if needle in t]
        if hit:
            return hit[0]
        time.sleep(0.5)
    return None


subprocess.run(['taskkill', '/f', '/im', 'MimiWallpapers.exe'], capture_output=True)
app = Application(backend='uia').start(EXE)
win = app.window(title='Mimi Wallpapers')
win.wait('visible', timeout=30)
win.set_focus()
time.sleep(4)
shot('01_launcher')
check('окно лаунчера открылось', win.exists())
check('каталог: 5 роликов', all(any(t2 in t for t in texts(win)) for t2 in
      ['KISS ME ANIMATION MEME', 'NUMBER ANIMATION MEME', 'YOU GOT CURVES', 'if i take you home', 'do not push']))
check('копирайт внизу', any('MimiFanStudio' in t for t in texts(win)))

# --- настройки и условия
win.child_window(title_re='.*Настройки', control_type='Button').click_input()
time.sleep(1.5)
sett = dialog('Настройки')
check('окно настроек', sett is not None)
check('в настройках есть выбор языка', any('Язык' in t for t in texts(sett)))
shot('02_settings')
sett.child_window(title_re='Авторские права.*', control_type='Button').click_input()
time.sleep(1.5)
legal = dialog('Авторские права и условия.*')
check('окно авторских прав и условий', legal is not None)
check('в условиях упомянуты MimiFanStudio и Typh', legal is not None and
      any('MimiFanStudio' in t for t in texts(legal)) and any('Typh' in t for t in texts(legal)))
shot('03_legal')
legal.type_keys('{ESC}')
time.sleep(0.8)
sett.type_keys('{ESC}')
time.sleep(0.8)

# --- ограничение: только Typh
edit = win.child_window(control_type='Edit')
edit.set_edit_text('https://youtu.be/dQw4w9WgXcQ')
win.child_window(title='Добавить', control_type='Button').click_input()
hit = wait_text(win, 'только ролики с канала Typh', 60)
check('чужой ролик не добавляется', bool(hit), (hit or '')[:90])
shot('04_only_typh')

# --- скачивание: полоса только растёт
win.child_window(title='YOU GOT CURVES ANIMATION MEME', control_type='Text', found_index=0).click_input()
time.sleep(1)
dl = win.child_window(title_re='.*Скачать.*', control_type='Button')
if dl.is_enabled():
    dl.click_input()
    bar = win.child_window(control_type='ProgressBar')
    vals, end = [], time.time() + 600
    while time.time() < end:
        try:
            vals.append(bar.iface_range_value.CurrentValue)
        except Exception:
            pass
        if wait_text(win, 'Скачано. Можно ставить', 0.1):
            break
        time.sleep(0.15)
    nums = [float(v) for v in vals]
    mono = all(b >= a for a, b in zip(nums, nums[1:]))
    check('скачивание завершилось', bool(wait_text(win, 'Скачано. Можно ставить', 5)))
    check('полоса загрузки только растёт', mono and len(nums) > 3, f'{len(nums)} замеров, {nums[:1]}…{nums[-1:]}')
else:
    check('скачивание (ролик уже скачан — пропуск)', True)
shot('05_downloaded')

# --- звук
s = win.child_window(title_re='.*Звук.*', control_type='Button')
before = s.window_text()
s.click_input()
time.sleep(0.8)
after = s.window_text()
s.click_input()
time.sleep(0.8)
check('переключатель звука', before != after and s.window_text() == before, f'{before} → {after}')

# --- обои
win.child_window(title_re='.*Поставить на обои', control_type='Button').click_input()
check('поставить на обои', bool(wait_text(win, 'Обои установлены', 10)))
time.sleep(4)
mpv = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-CimInstance Win32_Process -Filter \"Name='mpv.exe'\").CommandLine"], capture_output=True, text=True).stdout
check('Lively играет выбранный ролик', 'LGHCB5VUeOU' in mpv)

# --- экран блокировки
win.child_window(title_re='.*экран блокировки', control_type='Button').click_input()
time.sleep(3)
pick = dialog('Кадр для экрана блокировки')
check('окно выбора кадра', pick is not None)
shot('06_frame_picker')
pick.child_window(title_re='.*Поставить этот кадр', control_type='Button').click_input()
check('экран блокировки обновлён', bool(wait_text(win, 'Экран блокировки обновлён', 60)))
shot('07_final')

win.close()
print('\nИТОГ:', sum(ok for _, ok, _ in results), 'из', len(results))
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
