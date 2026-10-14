"""Установщик Mimi Wallpapers в стиле Mimi (анимированный фон, языки RU/EN/ES). © 2026 MimiFanStudio.

Собирается PyInstaller'ом в один exe; внутри: payload.zip (собранный лаунчер), setup_bg.webp, mimi.ico.
Ставит программу в папку пользователя (без прав администратора), создаёт ярлыки, регистрирует удаление,
при необходимости ставит mpv, yt-dlp и ffmpeg из официального каталога winget.
"""
import json
import os
import shutil
import subprocess
import time
import sys
import winreg
import zipfile

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QProgressBar, QPushButton, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget)

from common import (APP_NAME, CONFIG, DATA_DIR, NO_WINDOW, RES_DIR, STYLE, UNINSTALL_KEY, VIDEO_DIR,
                    WINGET_LINKS, AnimatedBackground, asset, fetch_thumbs, load_config, load_json, save_config, tool,
                    shortcut)
from i18n import COMPANY, LANGS, TERMS, VERSION, tr

DEFAULT_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Programs', 'Mimi Wallpapers')
def catalog_ids():
    return [v['id'] for v in load_json(os.path.join(RES_DIR, 'catalog.json'), [])]


def bundled_video():
    """Ролик, вшитый в установщик (только личная сборка): (id, видео, превью) или None."""
    for vid in catalog_ids():
        v = os.path.join(RES_DIR, vid + '.mkv')
        if os.path.exists(v):
            return vid, v, os.path.join(RES_DIR, vid + '_preview.mp4')
    return None


class ThumbLoader(QThread):
    """Загружает превью роликов Typh с YouTube для фона установщика."""
    loaded = Signal(list)

    def run(self):
        self.loaded.emit(fetch_thumbs(catalog_ids(), os.path.join(os.environ['TEMP'], 'MimiSetupThumbs')))


DEPS = [  # (название, id в winget, проверка)
    ('yt-dlp', 'yt-dlp.yt-dlp', lambda: os.path.exists(os.path.join(WINGET_LINKS, 'yt-dlp.exe'))),
    ('ffmpeg', 'yt-dlp.FFmpeg', lambda: os.path.exists(os.path.join(WINGET_LINKS, 'ffmpeg.exe'))),
    ('mpv', 'shinchiro.mpv', lambda: os.path.isabs(tool('mpv'))),        # плеер внутри движка обоев
]


def close_running(target):
    """Закрывает запущенный лаунчер и его фоновый ffmpeg: иначе файлы программы заняты (Permission denied)."""
    subprocess.run(['taskkill', '/f', '/im', 'MimiWallpapers.exe'], capture_output=True, creationflags=NO_WINDOW)
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    "Get-CimInstance Win32_Process -Filter \"Name='ffmpeg.exe'\" | Where-Object { $_.CommandLine -like '*"
                    + target.replace("'", "''") + "*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                   capture_output=True, creationflags=NO_WINDOW)


def extract_retry(z, info, target, tries=10):
    """Файл может освобождаться не сразу после закрытия процесса — пробуем ещё несколько раз."""
    for n in range(tries):
        try:
            return z.extract(info, target)
        except PermissionError:
            if n == tries - 1:
                raise
            time.sleep(0.5)


class Worker(QThread):
    progress = Signal(float, str)
    done = Signal(bool, str)

    def __init__(self, target, opts, lang):
        super().__init__()
        self.target, self.opts, self.lang = target, opts, lang

    def run(self):
        try:
            self._install()
            self.done.emit(True, '')
        except Exception as e:                                   # noqa: BLE001
            self.done.emit(False, str(e))

    def _install(self):
        t = lambda k, **kw: tr(k, self.lang, **kw)              # noqa: E731
        # 1. файлы (0–70 %)
        self.progress.emit(0, t('st_files'))
        os.makedirs(self.target, exist_ok=True)
        close_running(self.target)
        with zipfile.ZipFile(os.path.join(RES_DIR, 'payload.zip')) as z:
            names = z.infolist()
            total = sum(i.file_size for i in names) or 1
            doneb = 0
            for i in names:
                extract_retry(z, i, self.target)
                doneb += i.file_size
                self.progress.emit(70 * doneb / total, t('st_files'))
        exe = os.path.join(self.target, 'MimiWallpapers.exe')
        icon = asset('mimi.ico', 'icon.ico', base=self.target)
        # 2. ярлыки (70–74 %)
        self.progress.emit(70, t('st_shortcuts'))
        if self.opts['desktop']:
            shortcut(os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Mimi Wallpapers.lnk'), exe, icon=icon,
                     workdir=self.target)
        if self.opts['startmenu']:
            shortcut(os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs', 'Mimi Wallpapers.lnk'),
                     exe, icon=icon, workdir=self.target)
        # 3. регистрация и настройки (74–78 %)
        self.progress.emit(74, t('st_register'))
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
            for name, val in (('DisplayName', APP_NAME), ('DisplayVersion', VERSION), ('Publisher', COMPANY),
                              ('DisplayIcon', icon), ('InstallLocation', self.target),
                              ('UninstallString', f'"{exe}" --uninstall')):
                winreg.SetValueEx(k, name, 0, winreg.REG_SZ, val)
            winreg.SetValueEx(k, 'NoModify', 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, 'NoRepair', 0, winreg.REG_DWORD, 1)
            size_kb = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(self.target) for f in fs) // 1024
            winreg.SetValueEx(k, 'EstimatedSize', 0, winreg.REG_DWORD, int(size_kb))
        cfg = load_config()
        cfg['lang'] = self.lang
        cfg['autostart'] = self.opts['autostart']
        bv = bundled_video()
        if bv:
            self.progress.emit(75, t('st_video'))
            vid, vfile, prev = bv
            os.makedirs(VIDEO_DIR, exist_ok=True)
            shutil.copyfile(vfile, os.path.join(VIDEO_DIR, vid + '.mkv'))
            if os.path.exists(prev):
                shutil.copyfile(prev, os.path.join(VIDEO_DIR, vid + '_preview.mp4'))
            cfg['current'] = vid
        save_config(cfg)
        if self.opts['autostart']:
            startup = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut(os.path.join(startup, 'Mimi Wallpapers.lnk'), exe, '--engine', workdir=self.target)
        # 4. нужные программы через winget (78–100 %)
        if self.opts['deps']:
            step = 22 / len(DEPS)
            for n, (name, wid, ok) in enumerate(DEPS):
                base = 78 + step * n
                if ok():
                    self.progress.emit(base + step, t('st_dep_ok', n=name))
                    continue
                self.progress.emit(base + step * 0.1, t('st_dep', n=name))
                p = subprocess.Popen(['winget', 'install', '--id', wid, '-e', '--source', 'winget',
                                      '--accept-package-agreements', '--accept-source-agreements', '--silent'],
                                     creationflags=NO_WINDOW)
                tick = 0
                while p.poll() is None:                     # пока winget работает, полоса плавно ползёт в своём отрезке
                    tick += 1
                    self.progress.emit(base + step * min(0.9, 0.1 + tick * 0.01), t('st_dep', n=name))
                    self.msleep(500)
                self.progress.emit(base + step, t('st_dep', n=name))
        if load_json(CONFIG, {}).get('current') and os.path.isabs(tool('mpv')):
            # сразу запускаем движок: вшитый ролик (или прежние обои после обновления) появляется на рабочем столе
            self.progress.emit(99, t('st_video'))
            subprocess.Popen([exe, '--engine'], cwd=self.target, creationflags=NO_WINDOW | 0x00000008)
        self.progress.emit(100, '')


class Setup(AnimatedBackground):
    def __init__(self):
        super().__init__()
        self.lang = 'ru'
        self.setWindowTitle(tr('setup_title', self.lang))
        icon = asset('mimi.ico', 'icon.ico', base=RES_DIR)
        if icon:
            self.setWindowIcon(QIcon(icon))
        self.setFixedSize(960, 600)
        self.setStyleSheet(STYLE)
        personal = asset('setup_bg.webp', base=RES_DIR)
        self.play(personal or asset('bg_public.webp', base=RES_DIR))
        if not personal:                                   # публичная сборка: Mimi из превью роликов на YouTube
            self.thumbs = ThumbLoader()
            self.thumbs.loaded.connect(self._on_thumbs)
            self.thumbs.start()
        root = QHBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.addStretch()
        self.panel = QFrame()
        self.panel.setObjectName('panel')
        self.panel.setFixedWidth(520)
        root.addWidget(self.panel)
        self.pv = QVBoxLayout(self.panel)
        self.pv.setContentsMargins(26, 24, 26, 22)
        head = QHBoxLayout()
        self.face = face = QLabel()
        pm = QPixmap(asset('mimi.png', 'icon.png', base=RES_DIR))
        if not pm.isNull():
            face.setPixmap(pm.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.title = QLabel('Mimi Wallpapers')
        self.title.setFont(QFont('Segoe UI', 22, QFont.Black))
        self.title.setStyleSheet('color:#ffd1ea;')
        head.addWidget(face)
        head.addWidget(self.title)
        head.addStretch()
        self.pv.addLayout(head)
        self.stack = QStackedWidget()
        self.pv.addWidget(self.stack)
        foot = QLabel(f'© 2026 {COMPANY} · Mimi & animations © Typh')
        foot.setStyleSheet('color:#c9a4bd;font-size:10px;')
        self.pv.addWidget(foot, alignment=Qt.AlignCenter)
        self._page_lang()

    def t(self, k, **kw):
        return tr(k, self.lang, **kw)

    def _on_thumbs(self, paths):
        if not paths or not self.play_slides(paths):
            return
        pm = QPixmap(paths[0])
        if not pm.isNull():
            s = pm.height()
            sq = pm.copy((pm.width() - s) // 2, 0, s, s).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.face.setPixmap(sq)

    def _clear(self):
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

    def _page(self):
        self._clear()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        self.stack.addWidget(w)
        return lay

    def _nav(self, lay, back=None, next_text=None, next_cb=None):
        row = QHBoxLayout()
        if back:
            b = QPushButton(self.t('back'))
            b.setObjectName('ghost')
            b.clicked.connect(back)
            row.addWidget(b)
        row.addStretch()
        n = None
        if next_text:
            n = QPushButton(next_text)
            n.clicked.connect(next_cb)
            row.addWidget(n)
        lay.addLayout(row)
        return n

    # --- страницы
    def _page_lang(self):
        lay = self._page()
        h = QLabel('Выберите язык · Choose your language · Elige tu idioma')
        h.setWordWrap(True)
        h.setStyleSheet('font-size:14px;color:#ffe3f2;')
        lay.addWidget(h)
        lay.addSpacing(10)
        for code, name in LANGS.items():
            b = QPushButton(name)
            b.setObjectName('lang')
            b.clicked.connect(lambda _=False, c=code: self._set_lang(c))
            lay.addWidget(b)
        lay.addStretch()

    def _set_lang(self, code):
        self.lang = code
        self.setWindowTitle(self.t('setup_title'))
        self._page_terms()

    def _page_terms(self):
        lay = self._page()
        h = QLabel(self.t('welcome'))
        h.setStyleSheet('font-size:18px;font-weight:800;color:#ffd1ea;')
        p = QLabel(self.t('welcome_text'))
        p.setWordWrap(True)
        p.setStyleSheet('color:#ffe3f2;')
        text = QTextBrowser()
        text.setHtml(TERMS[self.lang])
        acc = QCheckBox(self.t('accept'))
        lay.addWidget(h)
        lay.addWidget(p)
        lay.addWidget(text, 1)
        lay.addWidget(acc)
        n = self._nav(lay, self._page_lang, self.t('next'), self._page_options)
        n.setEnabled(False)
        acc.toggled.connect(n.setEnabled)

    def _page_options(self):
        lay = self._page()
        lay.addWidget(QLabel(self.t('folder')))
        row = QHBoxLayout()
        self.path = QLineEdit(getattr(self, 'target', DEFAULT_DIR))
        br = QPushButton(self.t('browse'))
        br.setObjectName('ghost')
        br.clicked.connect(self._browse)
        row.addWidget(self.path)
        row.addWidget(br)
        lay.addLayout(row)
        lay.addSpacing(10)
        self.cb = {}
        for key, label in (('desktop', 'opt_desktop'), ('startmenu', 'opt_startmenu'), ('autostart', 'opt_autostart'),
                           ('deps', 'opt_deps')):
            c = QCheckBox(self.t(label))
            c.setChecked(True)
            c.setStyleSheet('font-size:13px;')
            self.cb[key] = c
            lay.addWidget(c)
        missing = [n for n, _, ok in DEPS if not ok()]
        if missing:
            info = QLabel('• ' + ', '.join(missing))
            info.setStyleSheet('color:#f7b3d9;font-size:11px;')
            lay.addWidget(info)
        lay.addStretch()
        self._nav(lay, self._page_terms, self.t('install'), self._page_progress)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, self.t('folder'), self.path.text())
        if d:
            self.path.setText(os.path.join(os.path.normpath(d), 'Mimi Wallpapers'))

    def _page_progress(self):
        self.target = self.path.text().strip() or DEFAULT_DIR
        opts = {k: c.isChecked() for k, c in self.cb.items()}
        lay = self._page()
        h = QLabel(self.t('installing'))
        h.setStyleSheet('font-size:18px;font-weight:800;color:#ffd1ea;')
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.status = QLabel()
        self.status.setStyleSheet('color:#ffe3f2;')
        self.pct = QLabel('0 %')
        self.pct.setStyleSheet('color:#f7b3d9;font-size:28px;font-weight:900;')
        lay.addStretch()
        lay.addWidget(h)
        lay.addWidget(self.pct)
        lay.addWidget(self.bar)
        lay.addWidget(self.status)
        lay.addStretch()
        self.worker = Worker(self.target, opts, self.lang)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.start()

    def _on_progress(self, pct, text):
        val = int(pct * 10)
        if val > self.bar.value():                                # только вперёд
            self.bar.setValue(val)
            self.pct.setText(f'{val // 10} %')
        if text:
            self.status.setText(text)

    def _on_done(self, ok, err):
        if not ok:
            self.status.setText(self.t('error') + ': ' + err)
            self.status.setWordWrap(True)
            return
        lay = self._page()
        h = QLabel(self.t('done_title'))
        h.setStyleSheet('font-size:26px;font-weight:900;color:#ffd1ea;')
        p = QLabel(self.t('done_text'))
        p.setWordWrap(True)
        p.setStyleSheet('color:#ffe3f2;font-size:14px;')
        self.launch = QCheckBox(self.t('launch'))
        self.launch.setChecked(True)
        lay.addStretch()
        lay.addWidget(h)
        lay.addWidget(p)
        lay.addSpacing(12)
        lay.addWidget(self.launch)
        lay.addStretch()
        self._nav(lay, None, self.t('finish'), self._finish)

    def _finish(self):
        if self.launch.isChecked():
            subprocess.Popen([os.path.join(self.target, 'MimiWallpapers.exe')], cwd=self.target)
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME + ' Setup')
    w = Setup()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
