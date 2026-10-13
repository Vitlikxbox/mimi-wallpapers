"""Mimi Wallpapers — лаунчер живых обоев с Mimi (персонаж аниматора Typh). © 2026 MimiFanStudio.

Каталог роликов Typh → скачивание в лучшем качестве (yt-dlp) → обои на рабочий стол (Lively Wallpaper),
кадр на экран блокировки, звук вкл/выкл, автозапуск, языки RU/EN/ES. Фон окна — зацикленное видео с Mimi.

Ключи запуска:  --apply-current (автозагрузка, без окна) · --download <id> · --uninstall
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import winreg

from PySide6.QtCore import QProcess, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSlider, QTextBrowser,
                               QVBoxLayout, QWidget)

from common import (APP_DIR, APP_NAME, CONFIG, DATA_DIR, FROZEN, LIVELY, NO_WINDOW, STYLE, THUMB_DIR, UNINSTALL_KEY,
                    VIDEO_DIR, AnimatedBackground, asset, load_config, load_json, run, save_config, shortcut, tool)
from i18n import COMPANY, LANGS, TERMS, TYPH_CHANNEL_ID, VERSION, tr


def catalog(cfg):
    base = load_json(os.path.join(APP_DIR, 'catalog.json'), [])
    ids = {v['id'] for v in base}
    return base + [v for v in cfg.get('extra', []) if v['id'] not in ids and v.get('channel_id') == TYPH_CHANNEL_ID]


def video_path(vid):
    for ext in ('mkv', 'webm', 'mp4'):
        p = os.path.join(VIDEO_DIR, f'{vid}.{ext}')
        if os.path.exists(p):
            return p
    return None


def preview_path(vid):
    return os.path.join(VIDEO_DIR, f'{vid}_preview.mp4')


def trim_credits(path, item):
    """Отрезает длинные титры в конце ролика: в каталоге у ролика может быть поле end (секунда начала титров).
    Без перекодирования (-c copy): качество и звук не меняются."""
    end = (item or {}).get('end')
    if not (end and path and os.path.exists(path)):
        return
    tmp = path + '.trim.mkv'
    run([tool('ffmpeg'), '-y', '-v', 'error', '-i', path, '-t', str(end), '-map', '0', '-c', 'copy', tmp], timeout=300)
    if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
        os.replace(tmp, path)


def preview_args(src, dst):
    return ['-y', '-v', 'error', '-i', src, '-an', '-vf', 'scale=-2:720', '-c:v', 'libx264', '-preset', 'veryfast',
            '-crf', '26', dst]


def dl_args(vid):
    args = ['-f', 'bv*+ba/b', '-S', 'res,fps,vbr', '--merge-output-format', 'mkv', '--no-playlist', '--newline',
            '-o', os.path.join(VIDEO_DIR, f'{vid}.%(ext)s')]
    ff = tool('ffmpeg')
    if os.path.isabs(ff):
        args += ['--ffmpeg-location', os.path.dirname(ff)]
    return args + [f'https://www.youtube.com/watch?v={vid}']


# ------------------------------------------------------------------ Lively и Windows
def lively_ok():
    return os.path.exists(LIVELY)


def lively_set(path):
    subprocess.Popen([LIVELY, 'setwp', '--file', path], creationflags=NO_WINDOW)


def lively_volume(v):
    subprocess.Popen([LIVELY, 'app', '--volume', str(int(v))], creationflags=NO_WINDOW)


LIVELY_SETTINGS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Lively Wallpaper', 'Settings.json')


def lively_audio_ok(only_desktop, volume):
    s = load_json(LIVELY_SETTINGS, {})
    return s.get('AudioOnlyOnDesktop') == only_desktop and s.get('AudioVolumeGlobal') == int(volume)


def lively_audio_setup(only_desktop, volume):
    """Звук обоев в Lively: «только на рабочем столе» вкл/выкл и общая громкость.
    Lively читает Settings.json при запуске и перезаписывает при выходе, поэтому: закрыть → править → запустить.
    Возвращает True, если Lively перезапускалась (обои она восстановит сама)."""
    if lively_audio_ok(only_desktop, volume) or not lively_ok():
        return False
    run(['taskkill', '/f', '/im', 'Lively.exe'])
    time.sleep(1.5)
    s = load_json(LIVELY_SETTINGS, {})
    if not s:
        return False
    s['AudioOnlyOnDesktop'] = bool(only_desktop)
    s['AudioVolumeGlobal'] = int(volume)
    with open(LIVELY_SETTINGS, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    subprocess.Popen(['explorer.exe', LIVELY])            # без прав администратора, как обычный запуск
    return True


LOCK_PS = r'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
function AwaitAction($op) { $m = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1; $m.Invoke($null, @($op)).Wait(-1) | Out-Null }
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType = WindowsRuntime] | Out-Null
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{path}')) ([Windows.Storage.StorageFile])
AwaitAction ([Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file))
'OK'
'''


def set_lockscreen(image):
    r = run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
             LOCK_PS.replace('{path}', image.replace("'", "''"))], timeout=60)
    return 'OK' in r.stdout, (r.stdout + r.stderr).strip()


def duration(video):
    d = run([tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', video])
    try:
        return float(d.stdout.strip())
    except ValueError:
        return 10.0


def extract_frame(video, out_png, seconds):
    run([tool('ffmpeg'), '-y', '-v', 'error', '-ss', f'{seconds:.2f}', '-i', video, '-frames:v', '1', out_png], timeout=120)
    return os.path.exists(out_png)


def startup_dir():
    return os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')


def set_autostart(enabled):
    lnk = os.path.join(startup_dir(), 'Mimi Wallpapers.lnk')
    old = os.path.join(startup_dir(), 'Живые обои Mimi.lnk')          # ярлык из самой первой версии
    if os.path.exists(old):
        os.remove(old)
    if not enabled:
        if os.path.exists(lnk):
            os.remove(lnk)
        return
    if FROZEN:
        shortcut(lnk, sys.executable, '--apply-current', workdir=APP_DIR)
    else:
        shortcut(lnk, sys.executable.replace('python.exe', 'pythonw.exe'),
                 f'"{os.path.abspath(__file__)}" --apply-current', workdir=APP_DIR)


def apply_current():
    cfg = load_config()
    p = video_path(cfg.get('current')) if cfg.get('current') else None
    if p and lively_ok():
        if 'Lively.exe' not in run(['tasklist', '/fi', 'imagename eq Lively.exe']).stdout:
            subprocess.Popen([LIVELY], creationflags=NO_WINDOW)
            time.sleep(8)
        if cfg.get('sound') and lively_audio_setup(not cfg.get('audio_everywhere', False), cfg.get('volume', 60)):
            time.sleep(8)
        lively_set(p)
        time.sleep(3)
        lively_volume(cfg.get('volume', 60) if cfg.get('sound') else 0)


BTN = {'yes': {'ru': 'Да', 'en': 'Yes', 'es': 'Sí'}, 'no': {'ru': 'Нет', 'en': 'No', 'es': 'No'}}


def top_box(text, lang, ask=True):
    """Окно удаления поверх всех окон (иначе оно может открыться за браузером) и с кнопками на языке программы."""
    box = QMessageBox(QMessageBox.Question if ask else QMessageBox.Information, APP_NAME, text)
    box.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    if ask:
        yes = box.addButton(BTN['yes'].get(lang, 'Yes'), QMessageBox.YesRole)
        box.setDefaultButton(box.addButton(BTN['no'].get(lang, 'No'), QMessageBox.NoRole))
    else:
        yes = box.addButton('OK', QMessageBox.AcceptRole)
    box.show()
    box.raise_()
    box.activateWindow()
    box.exec()
    return box.clickedButton() is yes


def uninstall():
    """Удаление программы (вызывается из «Программы и компоненты» или из настроек)."""
    app = QApplication.instance() or QApplication(sys.argv)
    lang = load_config().get('lang', 'ru')
    if not top_box(tr('uninstall_q', lang), lang):
        return
    wipe = top_box(tr('uninstall_data_q', lang), lang)
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    menu = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs')
    for lnk in (os.path.join(startup_dir(), 'Mimi Wallpapers.lnk'), os.path.join(desktop, 'Mimi Wallpapers.lnk'),
                os.path.join(menu, 'Mimi Wallpapers.lnk')):
        if os.path.exists(lnk):
            os.remove(lnk)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except OSError:
        pass
    top_box(tr('uninstall_done', lang), lang, ask=False)
    # другие окна лаунчера держат файлы программы — закрываем их (кроме этого процесса)
    run(['taskkill', '/f', '/im', 'MimiWallpapers.exe', '/fi', f'PID ne {os.getpid()}'])
    # фоновый ffmpeg лаунчера мог остаться (если окно закрыли аварийно) — он держит файлы программы
    run(['powershell', '-NoProfile', '-Command',
         "Get-CimInstance Win32_Process -Filter \"Name='ffmpeg.exe'\" | Where-Object { $_.CommandLine -like '*"
         + APP_DIR.replace("'", "''") + "*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"])
    targets = [f'"{APP_DIR}"'] + ([f'"{DATA_DIR}"'] if wipe else [])
    rm = ' & '.join(f'rmdir /s /q {t}' for t in targets)
    # строкой, а не списком: иначе Python экранирует кавычки так, что cmd не понимает путь с пробелом
    subprocess.Popen(f'cmd /c ping -n 3 127.0.0.1 >nul & {rm} & ping -n 3 127.0.0.1 >nul & {rm}',
                     creationflags=NO_WINDOW, cwd=os.environ.get('TEMP', 'C:\\'))


# ------------------------------------------------------------------ диалоги
class FramePicker(QDialog):
    """Выбор кадра для экрана блокировки: ползунок по ролику, превью из лёгкой копии."""

    def __init__(self, video, preview, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle(tr('frame_title', lang))
        self.setStyleSheet(STYLE)
        self.src = preview if os.path.exists(preview) else video
        self.dur = duration(self.src)
        self.tmp = os.path.join(DATA_DIR, '_frame_preview.jpg')
        lay = QVBoxLayout(self)
        self.img = QLabel()
        self.img.setFixedSize(768, 432)
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setStyleSheet('background:#2b1a33;border-radius:10px;')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, int(self.dur * 10))
        self.slider.setValue(int(self.dur * 4.5))
        self.time = QLabel()
        ok = QPushButton(tr('frame_ok', lang))
        ok.clicked.connect(self.accept)
        lay.addWidget(self.img)
        lay.addWidget(self.slider)
        row = QHBoxLayout()
        row.addWidget(self.time)
        row.addStretch()
        row.addWidget(ok)
        lay.addLayout(row)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._render)
        self.slider.valueChanged.connect(lambda _: self.timer.start(120))
        self._render()

    def seconds(self):
        return self.slider.value() / 10

    def _render(self):
        t, s = self.seconds(), tr('sec', self.lang)
        self.time.setText(f'{t:.1f} {s} {tr("of", self.lang)} {self.dur:.0f} {s}')
        run([tool('ffmpeg'), '-y', '-v', 'error', '-ss', f'{t:.2f}', '-i', self.src, '-frames:v', '1',
             '-vf', 'scale=768:-2', self.tmp], timeout=30)
        pm = QPixmap(self.tmp)
        if not pm.isNull():
            self.img.setPixmap(pm.scaled(768, 432, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class LegalDialog(QDialog):
    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('legal_title', lang))
        self.setStyleSheet(STYLE)
        self.resize(720, 620)
        lay = QVBoxLayout(self)
        text = QTextBrowser()
        text.setOpenExternalLinks(True)
        text.setHtml(TERMS[lang])
        close = QPushButton(tr('close', lang))
        close.clicked.connect(self.accept)
        lay.addWidget(text)
        lay.addWidget(close, alignment=Qt.AlignRight)


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        lang = cfg.get('lang', 'ru')
        self.setWindowTitle(tr('settings', lang).strip('⚙ '))
        self.setStyleSheet(STYLE)
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(tr('language', lang)))
        self.lang = QComboBox()
        for code, name in LANGS.items():
            self.lang.addItem(name, code)
        self.lang.setCurrentIndex(list(LANGS).index(lang))
        lay.addWidget(self.lang)
        lay.addSpacing(10)
        self.vol_label = QLabel()
        lay.addWidget(self.vol_label)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(cfg.get('volume', 60))
        self.vol.valueChanged.connect(lambda v: self.vol_label.setText(f"{tr('volume', lang)}: {v}%"))
        self.vol_label.setText(f"{tr('volume', lang)}: {self.vol.value()}%")
        lay.addWidget(self.vol)
        self.desk = QCheckBox(tr('audio_everywhere', lang))
        self.desk.setChecked(cfg.get('audio_everywhere', False))
        lay.addWidget(self.desk)
        lay.addSpacing(10)
        legal = QPushButton(tr('legal_link', lang))
        legal.setObjectName('ghost')
        legal.clicked.connect(lambda: LegalDialog(lang, self).exec())
        lay.addWidget(legal)
        self.uninst = QPushButton(tr('uninstall', lang))
        self.uninst.setObjectName('ghost')
        self.uninst.setVisible(FROZEN)
        lay.addWidget(self.uninst)
        lay.addWidget(QLabel(f'<span style="color:#b98fab">Mimi Wallpapers {VERSION} · © 2026 {COMPANY}</span>'))
        save = QPushButton(tr('save', lang))
        save.clicked.connect(self.accept)
        lay.addWidget(save, alignment=Qt.AlignRight)


# ------------------------------------------------------------------ главное окно
class Card(QFrame):
    clicked = Signal(str)

    def __init__(self, item, lang, parent=None):
        super().__init__(parent)
        self.item, self.lang = item, lang
        self.setObjectName('card')
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(240, 214)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        self.thumb = QLabel()
        self.thumb.setFixedSize(224, 126)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet('background:#2b1a33;border-radius:8px;')
        self.title = QLabel(item['title'])
        self.title.setWordWrap(True)
        self.title.setStyleSheet('font-weight:600;font-size:13px;color:white;')
        self.status = QLabel()
        self.status.setStyleSheet('font-size:11px;color:#f7b3d9;')
        lay.addWidget(self.thumb)
        lay.addWidget(self.title)
        lay.addWidget(self.status)
        self.refresh()

    def set_thumb(self, path):
        pm = QPixmap(path)
        if not pm.isNull():
            pm = pm.scaled(224, 126, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.thumb.setPixmap(pm.copy((pm.width() - 224) // 2, (pm.height() - 126) // 2, 224, 126))

    def refresh(self, current=None, selected=False):
        d = self.item.get('duration')
        st = tr('downloaded' if video_path(self.item['id']) else 'not_downloaded', self.lang)
        st += f" · {d} {tr('sec', self.lang)}" if d else ''
        if current == self.item['id']:
            st += ' · ' + tr('on_wallpaper', self.lang)
        self.status.setText(st)
        self.setProperty('sel', selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e):
        self.clicked.emit(self.item['id'])


class Launcher(AnimatedBackground):
    # этапы загрузки и их доли общей полосы: видео → звук → склейка → превью
    STAGES = {'video': (0, 80), 'audio': (80, 92), 'merge': (92, 96), 'preview': (96, 100)}

    def __init__(self):
        super().__init__()
        os.makedirs(VIDEO_DIR, exist_ok=True)
        os.makedirs(THUMB_DIR, exist_ok=True)
        self.cfg = load_config()
        self.lang = self.cfg.get('lang', 'ru') if self.cfg.get('lang') in LANGS else 'ru'
        self.items = catalog(self.cfg)
        self.selected = self.cfg.get('current') or (self.items[0]['id'] if self.items else None)
        self.cards, self.proc, self.dl_vid = {}, None, None
        self.stage, self.pct = 'video', 0.0
        self.setWindowTitle(APP_NAME)
        icon = asset('mimi.ico', 'icon.ico')
        if icon:
            self.setWindowIcon(QIcon(icon))
        self.resize(1180, 780)
        self.setStyleSheet(STYLE)
        self._build()
        self._load_thumbs()
        self._play_bg()
        if not lively_ok():
            QTimer.singleShot(500, lambda: QMessageBox.warning(self, APP_NAME, tr('no_lively', self.lang)))

    def t(self, key, **kw):
        return tr(key, self.lang, **kw)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 12)
        top = QHBoxLayout()
        logo = QLabel('Mimi Wallpapers')
        logo.setFont(QFont('Segoe UI', 24, QFont.Black))
        logo.setStyleSheet('color:#ffd1ea;')
        sub = QLabel(self.t('subtitle'))
        sub.setStyleSheet('color:#e8bcd6;font-size:12px;')
        col = QVBoxLayout()
        col.addWidget(logo)
        col.addWidget(sub)
        top.addLayout(col)
        top.addStretch()
        self.auto_cb = QCheckBox(self.t('autostart'))
        self.auto_cb.setChecked(self.cfg.get('autostart', True))
        self.auto_cb.toggled.connect(self.toggle_autostart)
        self.sound_btn = QPushButton()
        self.sound_btn.setObjectName('ghost')
        self.sound_btn.clicked.connect(self.toggle_sound)
        sett = QPushButton(self.t('settings'))
        sett.setObjectName('ghost')
        sett.clicked.connect(self.open_settings)
        for w in (self.auto_cb, self.sound_btn, sett):
            top.addWidget(w)
            top.addSpacing(8)
        root.addLayout(top)
        root.addSpacing(8)

        body = QHBoxLayout()
        left = QFrame()
        left.setObjectName('panel')
        lv = QVBoxLayout(left)
        add = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.t('url_hint'))
        add_btn = QPushButton(self.t('add'))
        add_btn.clicked.connect(self.add_url)
        add.addWidget(self.url_edit)
        add.addWidget(add_btn)
        lv.addLayout(add)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = QWidget()
        self.grid = QGridLayout(holder)
        self.grid.setSpacing(14)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(holder)
        lv.addWidget(scroll)
        body.addWidget(left, 3)

        right = QFrame()
        right.setObjectName('panel')
        right.setFixedWidth(330)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(16, 16, 16, 16)
        self.big = QLabel()
        self.big.setFixedSize(298, 168)
        self.big.setAlignment(Qt.AlignCenter)
        self.big.setStyleSheet('background:#2b1a33;border-radius:10px;')
        self.sel_title = QLabel()
        self.sel_title.setWordWrap(True)
        self.sel_title.setStyleSheet('font-size:17px;font-weight:800;color:#ffd1ea;')
        self.sel_info = QLabel()
        self.sel_info.setWordWrap(True)
        self.sel_info.setStyleSheet('color:#e8bcd6;font-size:12px;')
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        self.btn_dl = QPushButton(self.t('btn_download'))
        self.btn_apply = QPushButton(self.t('btn_apply'))
        self.btn_lock = QPushButton(self.t('btn_lock'))
        self.btn_del = QPushButton(self.t('btn_delete'))
        self.btn_del.setObjectName('ghost')
        self.btn_dl.clicked.connect(self.download)
        self.btn_apply.clicked.connect(self.apply)
        self.btn_lock.clicked.connect(self.lockscreen)
        self.btn_del.clicked.connect(self.delete)
        self.msg = QLabel()
        self.msg.setWordWrap(True)
        self.msg.setStyleSheet('color:#ffe3f2;font-size:12px;')
        for w in (self.big, self.sel_title, self.sel_info, self.progress, self.btn_dl, self.btn_apply,
                  self.btn_lock, self.btn_del, self.msg):
            rv.addWidget(w)
        rv.addStretch()
        note = QLabel(self.t('note'))
        note.setWordWrap(True)
        note.setStyleSheet('color:#b98fab;font-size:10px;')
        rv.addWidget(note)
        body.addWidget(right)
        root.addLayout(body)

        foot = QLabel(f'© 2026 {COMPANY} · Mimi Wallpapers {VERSION} · Mimi & animations © Typh · '
                      f'<a href="#legal" style="color:#ffb3dc">{self.t("legal_link")}</a>')
        foot.setStyleSheet('color:#c9a4bd;font-size:11px;')
        foot.linkActivated.connect(lambda _: LegalDialog(self.lang, self).exec())
        root.addWidget(foot, alignment=Qt.AlignCenter)
        self._fill_grid()
        self._update_sound_btn()
        self._select(self.selected)

    def _fill_grid(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.cards = {}
        for i, it in enumerate(self.items):
            c = Card(it, self.lang)
            c.clicked.connect(self._select)
            self.grid.addWidget(c, i // 3, i % 3)
            self.cards[it['id']] = c
            tp = os.path.join(THUMB_DIR, it['id'] + '.jpg')
            if os.path.exists(tp):
                c.set_thumb(tp)

    def _item(self, vid):
        return next((i for i in self.items if i['id'] == vid), None)

    def _select(self, vid):
        if not vid or not self._item(vid):
            return
        self.selected = vid
        it = self._item(vid)
        for k, c in self.cards.items():
            c.refresh(self.cfg.get('current'), k == vid)
        self.sel_title.setText(it['title'])
        have = video_path(vid)
        self.sel_info.setText(f"{self.t('author')}: {it.get('author', 'Typh')} · {it.get('duration', '?')} {self.t('sec')}\n"
                              + (f"{self.t('file')}: {os.path.basename(have)}" if have else self.t('not_yet')))
        tp = os.path.join(THUMB_DIR, vid + '.jpg')
        if os.path.exists(tp):
            pm = QPixmap(tp).scaled(298, 168, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.big.setPixmap(pm.copy((pm.width() - 298) // 2, (pm.height() - 168) // 2, 298, 168))
        busy = self.proc is not None
        self.btn_dl.setEnabled(not have and not busy)
        self.btn_apply.setEnabled(bool(have) and not busy)
        self.btn_lock.setEnabled(bool(have) and not busy)
        self.btn_del.setEnabled(bool(have) and not busy)

    def _update_sound_btn(self):
        self.sound_btn.setText(self.t('sound_on' if self.cfg.get('sound') else 'sound_off'))

    def _play_bg(self):
        for vid in [self.cfg.get('current')] + [i['id'] for i in self.items]:
            if vid and os.path.exists(preview_path(vid)):
                self.play(preview_path(vid))
                return
        bg = asset('launcher_bg.mp4')
        if bg:
            self.play(bg)
            return
        thumbs = [os.path.join(THUMB_DIR, i['id'] + '.jpg') for i in self.items]
        thumbs = [t for t in thumbs if os.path.exists(t)]
        if not self.play_slides(thumbs):                 # пока превью не загрузились — своя анимация
            self.play(asset('bg_public.webp'))
            QTimer.singleShot(6000, self._play_bg)

    def _load_thumbs(self):
        for it in self.items:
            tp = os.path.join(THUMB_DIR, it['id'] + '.jpg')
            if not os.path.exists(tp):
                QTimer.singleShot(50, lambda it=it, tp=tp: self._fetch_thumb(it, tp))

    def _fetch_thumb(self, it, tp):
        for name in ('maxresdefault', 'hqdefault'):
            try:
                urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{it['id']}/{name}.jpg", tp)
                break
            except Exception:
                continue
        if os.path.exists(tp) and it['id'] in self.cards:
            self.cards[it['id']].set_thumb(tp)
            if it['id'] == self.selected:
                self._select(self.selected)

    # --- добавление (только канал Typh)
    def add_url(self):
        m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})', self.url_edit.text().strip())
        if not m:
            self.msg.setText(self.t('bad_link'))
            return
        vid = m.group(1)
        if self._item(vid):
            self._select(vid)
            self.msg.setText(self.t('already'))
            return
        self.msg.setText(self.t('checking'))
        QApplication.processEvents()
        r = run([tool('yt-dlp'), '--skip-download', '--no-playlist', '--print',
                 '%(channel_id)s|%(channel)s|%(duration)s|%(title)s', f'https://www.youtube.com/watch?v={vid}'])
        parts = (r.stdout.strip().splitlines() or [''])[-1].split('|', 3)
        if len(parts) < 4:
            self.msg.setText(self.t('no_info'))
            return
        ch_id, ch, dur, title = parts
        if ch_id != TYPH_CHANNEL_ID:
            self.msg.setText(self.t('only_typh', ch=ch))
            return
        item = {'id': vid, 'title': title, 'duration': int(float(dur or 0)), 'author': ch, 'channel_id': ch_id,
                'url': f'https://www.youtube.com/watch?v={vid}'}
        self.cfg.setdefault('extra', []).append(item)
        save_config(self.cfg)
        self.items = catalog(self.cfg)
        self._fill_grid()
        self._load_thumbs()
        self._select(vid)
        self.url_edit.clear()
        self.msg.setText(self.t('added', t=title))

    # --- скачивание с ровной полосой
    def _set_progress(self, stage, frac):
        lo, hi = self.STAGES[stage]
        val = int((lo + (hi - lo) * max(0.0, min(1.0, frac))) * 10)
        if val > self.progress.value():                    # полоса только растёт
            self.progress.setValue(val)

    def download(self):
        self.dl_vid = self.selected
        self.stage, self.dests = 'video', 0
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.msg.setText(self.t('dl_video'))
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._dl_output)
        self.proc.finished.connect(lambda code, st: self._dl_done(code))
        self.proc.start(tool('yt-dlp'), dl_args(self.dl_vid))
        self._select(self.dl_vid)

    def _dl_output(self):
        for line in bytes(self.proc.readAllStandardOutput()).decode('utf-8', 'replace').splitlines():
            if 'Destination:' in line:
                self.dests += 1
                if self.dests >= 2:
                    self.stage = 'audio'
                    self.msg.setText(self.t('dl_audio'))
            elif '[Merger]' in line or 'Merging formats' in line:
                self.stage = 'merge'
                self._set_progress('merge', 0.2)
                self.msg.setText(self.t('dl_merge'))
            m = re.search(r'\[download\]\s+(\d+(?:\.\d+)?)%', line)
            if m and self.stage in ('video', 'audio'):
                self._set_progress(self.stage, float(m.group(1)) / 100)

    def _dl_done(self, code):
        vid, p = self.dl_vid, video_path(self.dl_vid)
        if code != 0 or not p:
            self.proc = None
            self.progress.setVisible(False)
            self.msg.setText(self.t('dl_fail'))
            self._select(vid)
            return
        self._set_progress('merge', 1)
        trim_credits(p, self._item(vid))
        self.msg.setText(self.t('dl_preview'))
        self.proc = QProcess(self)
        self.proc.finished.connect(lambda c, s: self._preview_done(vid))
        self.proc.start(tool('ffmpeg'), preview_args(p, preview_path(vid)))
        self.pv_timer = QTimer(self)
        self.pv_timer.timeout.connect(lambda: self._set_progress('preview', min(0.9, (self.progress.value() / 10 - 96 + 0.25) / 4)))
        self.pv_timer.start(400)

    def _preview_done(self, vid):
        self.pv_timer.stop()
        self.proc = None
        self.progress.setValue(1000)
        QTimer.singleShot(600, lambda: self.progress.setVisible(False))
        self.msg.setText(self.t('dl_done'))
        if self.frame is None or not self.cfg.get('current'):
            self._play_bg()
        self._select(vid)

    # --- применение
    def apply(self):
        p = video_path(self.selected)
        if not (p and lively_ok()):
            return
        lively_set(p)
        QTimer.singleShot(3000, self._sync_sound)
        self.cfg['current'] = self.selected
        save_config(self.cfg)
        if self.cfg.get('autostart', True):
            set_autostart(True)
        self._play_bg()
        self._select(self.selected)
        self.msg.setText(self.t('applied'))

    def lockscreen(self):
        p = video_path(self.selected)
        dlg = FramePicker(p, preview_path(self.selected), self.lang, self)
        if dlg.exec() != QDialog.Accepted:
            return
        png = os.path.join(DATA_DIR, f'lock_{self.selected}.png')
        self.msg.setText(self.t('frame_cut'))
        QApplication.processEvents()
        if not extract_frame(p, png, dlg.seconds()):
            self.msg.setText(self.t('frame_fail'))
            return
        ok, log = set_lockscreen(png)
        self.msg.setText(self.t('lock_ok') if ok else self.t('lock_fail') + '\n' + log[-200:])

    def delete(self):
        p = video_path(self.selected)
        if p and QMessageBox.question(self, APP_NAME, self.t('delete_q')) == QMessageBox.Yes:
            for f in (p, preview_path(self.selected)):
                if os.path.exists(f):
                    os.remove(f)
            self.msg.setText(self.t('deleted'))
            self._select(self.selected)

    def toggle_sound(self):
        self.cfg['sound'] = not self.cfg.get('sound')
        save_config(self.cfg)
        self._update_sound_btn()
        self._sync_sound()

    def _sync_sound(self):
        """Привести Lively к настройкам звука; если пришлось перезапустить Lively — вернуть обои и громкость."""
        vol = self.cfg.get('volume', 60)
        only_desk = not self.cfg.get('audio_everywhere', False)
        if self.cfg.get('sound') and not lively_audio_ok(only_desk, vol):
            self.msg.setText(self.t('sound_setup'))
            QApplication.processEvents()
            if lively_audio_setup(only_desk, vol):
                cur = video_path(self.cfg.get('current')) if self.cfg.get('current') else None
                QTimer.singleShot(7000, lambda: (cur and lively_set(cur)))
                QTimer.singleShot(10000, lambda: (lively_volume(vol), self.msg.setText('')))
                return
        lively_volume(vol if self.cfg.get('sound') else 0)

    def toggle_autostart(self, on):
        self.cfg['autostart'] = on
        save_config(self.cfg)
        set_autostart(on)

    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        dlg.uninst.clicked.connect(lambda: (dlg.reject(), self.close(),
                                            subprocess.Popen([sys.executable, '--uninstall'])))
        if dlg.exec() != QDialog.Accepted:
            return
        self.cfg['volume'] = dlg.vol.value()
        self.cfg['audio_everywhere'] = dlg.desk.isChecked()
        new_lang = dlg.lang.currentData()
        save_config(self.cfg)
        if self.cfg.get('sound'):
            self._sync_sound()
        if new_lang != self.lang:
            self.cfg['lang'] = new_lang
            save_config(self.cfg)
            QMessageBox.information(self, APP_NAME, tr('restart_lang', new_lang))
            args = sys.argv[1:] if FROZEN else [os.path.abspath(__file__)]
            QProcess.startDetached(sys.executable, args)
            self.close()


def cli_download(vid):
    os.makedirs(VIDEO_DIR, exist_ok=True)
    subprocess.run([tool('yt-dlp')] + [a for a in dl_args(vid) if a != '--newline'], creationflags=NO_WINDOW)
    p = video_path(vid)
    if p:
        trim_credits(p, next((i for i in catalog(load_config()) if i['id'] == vid), None))
        run([tool('ffmpeg')] + preview_args(p, preview_path(vid)), timeout=600)
    return p


def main():
    if '--apply-current' in sys.argv:
        apply_current()
        return
    if '--download' in sys.argv:
        print(cli_download(sys.argv[sys.argv.index('--download') + 1]))
        return
    if '--uninstall' in sys.argv:
        uninstall()
        return
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    w = Launcher()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
