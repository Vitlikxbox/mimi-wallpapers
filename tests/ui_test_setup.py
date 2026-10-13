"""Автотест установщика и удаления Mimi Wallpapers (pywinauto, UI Automation)."""
import os
import subprocess
import sys
import time
import winreg

from pywinauto import Application, Desktop

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP = next(p for p in (os.path.join(ROOT, 'installer', n) for n in ('MimiWallpapers_Setup.exe', 'MimiWallpapers_Setup_public.exe')) if os.path.exists(p))
APP_DIR = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Mimi Wallpapers')
EXE = os.path.join(APP_DIR, 'MimiWallpapers.exe')
KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\MimiWallpapers'
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots')
os.makedirs(SHOTS, exist_ok=True)
results = []


def check(name, ok, info=''):
    results.append((name, ok))
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {info}' if info else ''), flush=True)


def shot(name):
    from PIL import ImageGrab
    ImageGrab.grab().save(os.path.join(SHOTS, name + '.png'))


def reg_exists():
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY))
        return True
    except OSError:
        return False


def click(win, title_re, ctype='Button', timeout=20):
    c = win.child_window(title_re=title_re, control_type=ctype)
    c.wait('visible enabled', timeout=timeout)
    c.click_input()
    time.sleep(0.8)


def msgbox_click(button_re, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for w in Desktop(backend='uia').windows():
            try:
                for b in w.descendants(control_type='Button'):
                    import re
                    if re.match(button_re, b.window_text()) and w.window_text() == 'Mimi Wallpapers':
                        b.invoke()          # без мыши: не промахнёмся, даже если окно чем-то закрыто
                        time.sleep(1)
                        return True
            except Exception:
                pass
        time.sleep(0.5)
    return False


def open_setup():
    app = Application(backend='uia').start(SETUP)
    # onefile: окно открывает дочерний процесс, поэтому ищем окно на всём рабочем столе
    win = Desktop(backend='uia').window(title_re='(Установка|Mimi Wallpapers Setup|Instalación).*')
    win.wait('visible', timeout=90)          # onefile распаковывается несколько секунд
    win.set_focus()
    time.sleep(2)
    return app, win


# ---------- 1. удаление (видео оставляем)
subprocess.run(['taskkill', '/f', '/im', 'MimiWallpapers.exe'], capture_output=True)
subprocess.Popen([EXE, '--uninstall'])
check('удаление: вопрос «Удалить?» → Да', msgbox_click(r'&?(Yes|Да|Sí)'))
check('удаление: «Удалить и видео?» → Нет', msgbox_click(r'&?(No|Нет)'))
check('удаление: сообщение «удалён» → OK', msgbox_click(r'&?(OK|ОК)'))
time.sleep(5)
check('папка программы удалена', not os.path.exists(EXE))
check('запись в «Программах и компонентах» удалена', not reg_exists())
check('скачанные видео сохранились', os.path.isdir(os.path.expandvars(r'%LOCALAPPDATA%\MimiWallpapers\videos')))

# ---------- 2. экраны на английском и испанском
for lang, accept, title_terms in (('English', 'I accept.*', 'Welcome!'), ('Español', 'Acepto.*', '¡Bienvenido!')):
    app, win = open_setup()
    if lang == 'English':
        shot('10_setup_lang')
    click(win, lang)
    ok = win.child_window(title=title_terms, control_type='Text').exists(timeout=5)
    check(f'установщик: страница условий на {lang}', ok)
    shot(f'11_setup_terms_{lang}')
    nxt = win.child_window(title_re='(Next|Siguiente).*', control_type='Button')
    check(f'«Далее» заблокирована без согласия ({lang})', not nxt.is_enabled())
    click(win, accept, 'CheckBox')
    check(f'после согласия «Далее» доступна ({lang})', nxt.is_enabled())
    nxt.click_input()
    time.sleep(1)
    shot(f'12_setup_options_{lang}')
    win.close()
    time.sleep(2)

# ---------- 3. полная установка на русском
app, win = open_setup()
click(win, 'Русский')
click(win, 'Я принимаю.*', 'CheckBox')
click(win, 'Далее.*')
shot('13_setup_options_ru')
click(win, 'Установить')
time.sleep(1)
shot('14_setup_progress')
done = win.child_window(title='Готово!', control_type='Text')
check('установка завершилась', done.exists(timeout=300))
shot('15_setup_done')
click(win, 'Запустить Mimi Wallpapers', 'CheckBox')        # снимаем галочку запуска
click(win, 'Готово')
time.sleep(2)
check('файлы программы на месте', os.path.exists(EXE) and os.path.exists(os.path.join(APP_DIR, 'catalog.json')))
check('программа зарегистрирована для удаления', reg_exists())
desk = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Mimi Wallpapers.lnk')
startup = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Mimi Wallpapers.lnk')
check('ярлык на рабочем столе', os.path.exists(desk))
check('автозапуск', os.path.exists(startup))

print('\nИТОГ:', sum(ok for _, ok in results), 'из', len(results))
sys.exit(0 if all(ok for _, ok in results) else 1)
