"""Общее для лаунчера и установщика Mimi Wallpapers: пути, инструменты, стиль, анимированный фон."""
import json
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QColor, QImage, QMovie, QPainter
from PySide6.QtWidgets import QWidget

APP_NAME = 'Mimi Wallpapers'
FROZEN = getattr(sys, 'frozen', False)
# папка с файлами программы; у собранного установщика PyInstaller распаковывает данные в sys._MEIPASS
RES_DIR = getattr(sys, '_MEIPASS', None) or (os.path.dirname(sys.executable) if FROZEN
                                            else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', APP_DIR), 'MimiWallpapers')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
THUMB_DIR = os.path.join(DATA_DIR, 'thumbs')
CONFIG = os.path.join(DATA_DIR, 'config.json')
LIVELY = r'C:\Program Files\Lively Wallpaper\Lively.exe'
WINGET_LINKS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WinGet', 'Links')
UNINSTALL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\MimiWallpapers'
NO_WINDOW = 0x08000000


def asset(*names, base=None):
    """Первый существующий файл из списка: личное оформление с Mimi, иначе публичное (assets/)."""
    for n in names:
        for d in ((base,) if base else (APP_DIR, RES_DIR, os.path.join(APP_DIR, 'assets'), os.path.join(RES_DIR, 'assets'))):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return ''


def tool(name):
    """yt-dlp / ffmpeg / ffprobe: из папки программы, из папки winget или из PATH."""
    for d in (os.path.join(APP_DIR, 'tools'), APP_DIR, WINGET_LINKS):
        p = os.path.join(d, name + '.exe')
        if os.path.exists(p):
            return p
    return shutil.which(name) or name


def run(args, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          timeout=timeout, creationflags=NO_WINDOW)


def load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def load_config():
    cfg = {'sound': False, 'volume': 60, 'current': None, 'extra': [], 'autostart': True, 'lang': 'ru'}
    cfg.update(load_json(CONFIG, {}))
    return cfg


def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def shortcut(lnk, target, args='', icon='', workdir=''):
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');$s.TargetPath='{target}';"
          f"$s.Arguments='{args}';$s.WorkingDirectory='{workdir}';"
          + (f"$s.IconLocation='{icon}';" if icon else '') + "$s.Save()")
    run(['powershell', '-NoProfile', '-Command', ps])


STYLE = '''
QWidget { color: white; font-family: "Segoe UI"; }
#panel { background: rgba(25, 12, 32, 205); border-radius: 16px; }
#card { background: rgba(40, 20, 50, 190); border-radius: 12px; border: 2px solid transparent; }
#card:hover { border: 2px solid rgba(247, 140, 200, 140); }
#card[sel="true"] { border: 2px solid #f78cc8; background: rgba(80, 30, 80, 210); }
QPushButton { background: #f78cc8; color: #2a0f2a; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; }
QPushButton:hover { background: #ffa9d8; }
QPushButton:disabled { background: #6b4a63; color: #b9a3b4; }
QPushButton#ghost { background: rgba(255,255,255,30); color: white; }
QPushButton#ghost:hover { background: rgba(255,255,255,55); }
QPushButton#lang { background: rgba(255,255,255,28); color: white; font-size: 18px; padding: 18px; border-radius: 14px; }
QPushButton#lang:hover { background: #f78cc8; color: #2a0f2a; }
QLineEdit, QComboBox { background: rgba(255,255,255,25); border: 1px solid rgba(255,255,255,60); border-radius: 8px; padding: 8px; }
QComboBox QAbstractItemView { background: #2b1a33; color: white; selection-background-color: #f78cc8; }
QProgressBar { background: rgba(255,255,255,25); border-radius: 7px; height: 14px; text-align: center; color: white; }
QProgressBar::chunk { background: #f78cc8; border-radius: 7px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QTextBrowser { background: rgba(0,0,0,70); border: 1px solid rgba(255,255,255,40); border-radius: 10px; padding: 8px; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,40); border-radius: 3px; }
QSlider::handle:horizontal { background: #f78cc8; width: 16px; margin: -6px 0; border-radius: 8px; }
QDialog { background: #1f1026; }
a { color: #ffb3dc; }
'''


class AnimatedBackground(QWidget):
    """Фон окна с Mimi: видео через ffmpeg (если есть) или анимированный WebP через QMovie (в установщике)."""
    BW, BH = 960, 540

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = None
        self.buf = b''
        self.bg = None
        self.movie = None

    def play(self, path):
        if not (path and os.path.exists(path)):
            return
        self.stop()
        if path.lower().endswith(('.webp', '.gif')):
            self.movie = QMovie(path, parent=self)
            self.movie.frameChanged.connect(lambda _: self._set(self.movie.currentImage()))
            self.movie.start()
            return
        self.buf = b''
        self.bg = QProcess(self)
        self.bg.readyReadStandardOutput.connect(self._on_data)
        vf = f'fps=30,scale={self.BW}:{self.BH}:force_original_aspect_ratio=increase,crop={self.BW}:{self.BH}'
        self.bg.start(tool('ffmpeg'), ['-v', 'quiet', '-stream_loop', '-1', '-re', '-i', path, '-an', '-vf', vf,
                                       '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'])

    def stop(self):
        if self.bg is not None:
            self.bg.kill()
            self.bg.waitForFinished(1000)
            self.bg = None
        if self.movie is not None:
            self.movie.stop()
            self.movie = None

    def _set(self, img):
        if not img.isNull():
            self.frame = img
            self.update()

    def _on_data(self):
        self.buf += bytes(self.bg.readAllStandardOutput())
        size = self.BW * self.BH * 3
        if len(self.buf) >= size:
            n = len(self.buf) // size
            raw = self.buf[(n - 1) * size:n * size]
            self.buf = self.buf[n * size:]
            self._set(QImage(raw, self.BW, self.BH, self.BW * 3, QImage.Format_RGB888).copy())

    def closeEvent(self, e):
        self.stop()
        super().closeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#1a0f1f'))
        if self.frame is not None:
            img = self.frame.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.drawImage((self.width() - img.width()) // 2, (self.height() - img.height()) // 2, img)
        p.fillRect(self.rect(), QColor(20, 8, 26, 120))
