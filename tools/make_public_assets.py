"""Публичное оформление Mimi Wallpapers (своя графика, без кадров из анимаций Typh):
assets/icon.png, assets/icon.ico — иконка; assets/bg_public.webp — анимированный фон (розовый градиент и сердечки).
Используется, если нет личных файлов launcher_bg.mp4 / setup_bg.webp / mimi.ico (их в репозиторий не кладём)."""
import math
import os
import random
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, \
    QRadialGradient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets')
W, H, FRAMES, FPS = 960, 540, 90, 15


def heart(cx, cy, s):
    p = QPainterPath()
    p.moveTo(cx, cy + s * 0.35)
    p.cubicTo(cx - s * 1.0, cy - s * 0.35, cx - s * 0.45, cy - s * 1.0, cx, cy - s * 0.45)
    p.cubicTo(cx + s * 0.45, cy - s * 1.0, cx + s * 1.0, cy - s * 0.35, cx, cy + s * 0.35)
    return p


def icon():
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 256, 256)
    g.setColorAt(0, QColor('#ffb3dc'))
    g.setColorAt(1, QColor('#b03a8a'))
    p.setBrush(QBrush(g))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(8, 8, 240, 240), 56, 56)
    p.setBrush(QColor(255, 255, 255, 235))
    p.drawPath(heart(128, 150, 92))
    p.setPen(QColor('#b03a8a'))
    f = QFont('Segoe UI', 64, QFont.Black)
    p.setFont(f)
    p.drawText(QRectF(0, 70, 256, 120), Qt.AlignCenter, 'M')
    p.end()
    img.save(os.path.join(OUT, 'icon.png'))
    img.save(os.path.join(OUT, 'icon.ico'))


def background():
    rnd = random.Random(7)
    hearts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(10, 34), rnd.uniform(0.6, 1.6), rnd.uniform(0, 6.28))
              for _ in range(26)]
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES
        img = QImage(W, H, QImage.Format_RGB32)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, W, H)
        g.setColorAt(0, QColor.fromHsvF((0.88 + 0.03 * math.sin(6.28 * t)) % 1, 0.55, 0.55))
        g.setColorAt(1, QColor.fromHsvF(0.78, 0.65, 0.25))
        p.fillRect(0, 0, W, H, g)
        for k in range(3):                      # мягкие световые пятна
            cx = W * (0.25 + 0.5 * k / 2) + 80 * math.sin(6.28 * (t + k / 3))
            rg = QRadialGradient(QPointF(cx, H * 0.5), 260)
            rg.setColorAt(0, QColor(255, 180, 220, 70))
            rg.setColorAt(1, QColor(255, 180, 220, 0))
            p.fillRect(0, 0, W, H, rg)
        p.setPen(Qt.NoPen)
        for x, y, s, sp, ph in hearts:          # сердечки плывут вверх, бесшовный цикл
            yy = (y - t * H * sp) % (H + 80) - 40
            xx = x + 18 * math.sin(6.28 * t * 2 + ph)
            p.setBrush(QColor(255, 210, 235, int(90 + 70 * math.sin(6.28 * t + ph) ** 2)))
            p.drawPath(heart(xx, yy, s))
        p.end()
        frames.append(img)
    tmp = os.path.join(OUT, '_frames')
    os.makedirs(tmp, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(tmp, f'{i:03d}.png'))
    return tmp


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    os.makedirs(OUT, exist_ok=True)
    icon()
    frames = background()
    import shutil
    import subprocess
    ffmpeg = shutil.which('ffmpeg') or os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe')
    subprocess.run([ffmpeg, '-y', '-v', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%03d.png'),
                    '-c:v', 'libwebp', '-q:v', '70', '-loop', '0', os.path.join(OUT, 'bg_public.webp')], check=True)
    shutil.rmtree(frames)
    print('assets/icon.png, assets/icon.ico, assets/bg_public.webp')
