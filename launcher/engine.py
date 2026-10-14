"""Движок живых обоев Mimi Wallpapers (вместо Lively Wallpaper).

Запускается как `MimiWallpapers.exe --engine` и живёт в фоне без окна:
  * на каждый монитор — свой mpv (аппаратное декодирование, бесконечный повтор);
  * окно mpv встраивается в рабочий стол под ярлыки (Progman/WorkerW, в том числе новая схема Windows 11 24H2);
  * звук: выкл / только на пустом рабочем столе / везде (config.json: sound, volume, audio_everywhere);
  * пауза, когда на мониторе открыта полноэкранная игра или видео (экономит видеокарту);
  * следит за config.json: лаунчер просто меняет настройки, движок сам переключает обои и звук;
  * если Проводник перезапустился — заново встраивает обои.
Один экземпляр на пользователя (именованный мьютекс). mpv привязаны к движку через Job Object и закрываются вместе с ним.
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import traceback
from ctypes import wintypes as W

from common import APP_DIR, CONFIG, DATA_DIR, FROZEN, NO_WINDOW, VIDEO_DIR, load_config, tool
import threading

u32 = ctypes.WinDLL('user32', use_last_error=True)
k32 = ctypes.WinDLL('kernel32', use_last_error=True)

for f in ('FindWindowW', 'FindWindowExW', 'GetParent', 'GetForegroundWindow', 'SetParent', 'MonitorFromWindow',
          'GetAncestor'):
    getattr(u32, f).restype = W.HWND if f != 'MonitorFromWindow' else W.HMONITOR
u32.FindWindowExW.argtypes = [W.HWND, W.HWND, W.LPCWSTR, W.LPCWSTR]
u32.SetParent.argtypes = [W.HWND, W.HWND]
u32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
u32.GetWindowLongPtrW.argtypes = [W.HWND, ctypes.c_int]
u32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
u32.SetWindowLongPtrW.argtypes = [W.HWND, ctypes.c_int, ctypes.c_ssize_t]
u32.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
u32.SendMessageTimeoutW.argtypes = [W.HWND, ctypes.c_uint, W.WPARAM, W.LPARAM, ctypes.c_uint, ctypes.c_uint,
                                    ctypes.POINTER(ctypes.c_size_t)]
u32.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
u32.MonitorFromWindow.argtypes = [W.HWND, W.DWORD]
u32.GetMonitorInfoW.argtypes = [W.HMONITOR, ctypes.c_void_p]
u32.MapWindowPoints.argtypes = [W.HWND, W.HWND, ctypes.c_void_p, ctypes.c_uint]
u32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
k32.CreateMutexW.restype = W.HANDLE
k32.CreateJobObjectW.restype = W.HANDLE
k32.OpenProcess.restype = W.HANDLE

MUTEX_NAME = 'Local\\MimiWallpapersEngine'
LOG = os.path.join(DATA_DIR, 'engine.log')
GWL_STYLE, GWL_EXSTYLE = -16, -20
WS_CHILD, WS_VISIBLE, WS_POPUP, WS_CAPTION, WS_THICKFRAME = 0x40000000, 0x10000000, 0x80000000, 0x00C00000, 0x00040000
WS_EX_APPWINDOW, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x40000, 0x80, 0x08000000
SWP_NOACTIVATE, SWP_SHOWWINDOW, SWP_FRAMECHANGED = 0x10, 0x40, 0x20
SHELL_CLASSES = {'Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd', 'SHELLDLL_DefView', ''}
DESKTOP_CLASSES = {'Progman', 'WorkerW', 'SHELLDLL_DefView'}


class MONITORINFO(ctypes.Structure):
    _fields_ = [('cbSize', W.DWORD), ('rcMonitor', W.RECT), ('rcWork', W.RECT), ('dwFlags', W.DWORD)]


def log(*a):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')
    except OSError:
        pass


def cls(h):
    b = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, b, 256)
    return b.value


def rect(h):
    r = W.RECT()
    u32.GetWindowRect(h, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def monitors():
    """Прямоугольники мониторов (основной — первым)."""
    out = []
    proc = ctypes.WINFUNCTYPE(W.BOOL, W.HMONITOR, W.HDC, ctypes.POINTER(W.RECT), W.LPARAM)

    def cb(hmon, _hdc, _r, _l):
        mi = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
        u32.GetMonitorInfoW(hmon, ctypes.byref(mi))
        r = mi.rcMonitor
        out.append(((r.left, r.top, r.right, r.bottom), bool(mi.dwFlags & 1)))
        return True
    u32.EnumDisplayMonitors(None, None, proc(cb), 0)
    out.sort(key=lambda m: not m[1])
    return [m[0] for m in out]


def desktop_host():
    """Окно, в которое встраиваются обои, и окно, под которым они должны лежать (ярлыки)."""
    progman = u32.FindWindowW('Progman', None)
    res = ctypes.c_size_t()
    # просим Проводник создать слой WorkerW между ярлыками и картинкой рабочего стола
    u32.SendMessageTimeoutW(progman, 0x052C, 0xD, 0x1, 0, 1000, ctypes.byref(res))
    u32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, ctypes.byref(res))
    defview = u32.FindWindowExW(progman, None, 'SHELLDLL_DefView', None)
    if defview:
        # Windows 11 24H2+: ярлыки и WorkerW — дочерние окна Progman; обои кладём в Progman сразу под ярлыки
        return progman, defview
    # старая схема: ярлыки в одном из верхних WorkerW, обои — в следующий за ним WorkerW
    w = u32.FindWindowExW(None, None, 'WorkerW', None)
    while w:
        if u32.FindWindowExW(w, None, 'SHELLDLL_DefView', None):
            nxt = u32.FindWindowExW(None, w, 'WorkerW', None)
            return (nxt or progman), None
        w = u32.FindWindowExW(None, w, 'WorkerW', None)
    return progman, None


def children(host):
    """Дочерние окна сверху вниз (по порядку наложения)."""
    out, c = [], u32.FindWindowExW(host, None, None, None)
    while c:
        out.append(c)
        c = u32.FindWindowExW(host, c, None, None)
    return out


def misplaced(host, hwnd, below):
    """Видео не на своём месте: поверх ярлыков (закрывает рабочий стол) или под слоем WorkerW (видео не видно)."""
    order = children(host)
    if hwnd not in order:
        return False
    above = order[:order.index(hwnd)]
    return bool(below and below not in above) or any(cls(c) == 'WorkerW' for c in above)


WNDPROC_ADDR = ctypes.cast(u32.DefWindowProcW, ctypes.c_void_p).value
HOST_CLASS = 'MimiWallpaperHost'
_class_ready = False


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [('cbSize', W.UINT), ('style', W.UINT), ('lpfnWndProc', ctypes.c_void_p), ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int), ('hInstance', W.HINSTANCE), ('hIcon', W.HICON), ('hCursor', W.HANDLE),
                ('hbrBackground', W.HBRUSH), ('lpszMenuName', W.LPCWSTR), ('lpszClassName', W.LPCWSTR),
                ('hIconSm', W.HICON)]


u32.CreateWindowExW.restype = W.HWND
u32.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
u32.RegisterClassExW.argtypes = [ctypes.c_void_p]
u32.DestroyWindow.argtypes = [W.HWND]
k32.GetModuleHandleW.restype = W.HMODULE
k32.GetModuleHandleW.argtypes = [W.LPCWSTR]


def create_host(parent, below, mon):
    """Окно-подложка для видео прямо внутри рабочего стола: у плеера нет своего окна,
    поэтому его не видно на панели задач и в Alt+Tab и его нельзя случайно закрыть."""
    global _class_ready
    hinst = k32.GetModuleHandleW(None)
    if not _class_ready:
        wc = WNDCLASSEXW(cbSize=ctypes.sizeof(WNDCLASSEXW), lpfnWndProc=WNDPROC_ADDR, hInstance=hinst,
                         hbrBackground=ctypes.windll.gdi32.GetStockObject(4), lpszClassName=HOST_CLASS)  # BLACK_BRUSH
        u32.RegisterClassExW(ctypes.byref(wc))
        _class_ready = True
    pt = (W.POINT * 2)(W.POINT(mon[0], mon[1]), W.POINT(mon[2], mon[3]))
    u32.MapWindowPoints(None, parent, pt, 2)               # экранные координаты → координаты внутри рабочего стола
    h = u32.CreateWindowExW(WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW, HOST_CLASS, 'Mimi Wallpaper',
                            WS_CHILD | WS_VISIBLE | 0x02000000 | 0x04000000,  # CLIPCHILDREN | CLIPSIBLINGS
                            pt[0].x, pt[0].y, pt[1].x - pt[0].x, pt[1].y - pt[0].y, parent, None, hinst, None)
    if h:
        u32.SetWindowPos(h, below or None, 0, 0, 0, 0, SWP_NOACTIVATE | 0x1 | 0x2)
    return h


def pump(seconds):
    """Ждать, обрабатывая сообщения своих окон (окна живут внутри Проводника — без этого он бы подвисал)."""
    end = time.time() + seconds
    msg = W.MSG()
    while True:
        while u32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):   # PM_REMOVE
            u32.TranslateMessage(ctypes.byref(msg))
            u32.DispatchMessageW(ctypes.byref(msg))
        left = end - time.time()
        if left <= 0:
            return
        u32.MsgWaitForMultipleObjects(0, None, False, int(left * 1000), 0x04FF)  # QS_ALLINPUT


class Job:
    """Все mpv в одном Job Object: если движок закроют (или он упадёт), Windows закроет и mpv."""

    def __init__(self):
        self.h = k32.CreateJobObjectW(None, None)

        class LIMIT(ctypes.Structure):
            # JOBOBJECT_EXTENDED_LIMIT_INFORMATION (x64): 144 байта, LimitFlags по смещению 16
            _fields_ = [('a', ctypes.c_int64 * 2), ('LimitFlags', W.DWORD), ('b', ctypes.c_byte * 124)]
        info = LIMIT()
        info.LimitFlags = 0x2000                               # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(self.h, 9, ctypes.byref(info), ctypes.sizeof(info)):
            log('Job Object не настроен, ошибка', ctypes.get_last_error())

    def add(self, pid):
        hp = k32.OpenProcess(0x1F0FFF, False, pid)
        if hp:
            if not k32.AssignProcessToJobObject(self.h, hp):
                log('mpv не привязан к Job Object, ошибка', ctypes.get_last_error())
            k32.CloseHandle(hp)


class Player:
    """Один mpv на одном мониторе."""

    def __init__(self, idx, video, mon, cfg, job, parent, below):
        self.idx, self.video, self.mon, self.parent = idx, video, mon, parent
        self.pipe = rf'\\.\pipe\mimi-wallpaper-{os.getpid()}-{idx}-{int(time.time() * 1000)}'
        self.hwnd = create_host(parent, below, mon)
        self.state = {}
        args = [tool('mpv'), video, '--config=no', f'--wid={self.hwnd or 0}', '--loop-file=inf', '--hwdec=auto-safe',
                '--panscan=1.0', '--osc=no', '--osd-level=0', '--input-default-bindings=no',
                '--input-vo-keyboard=no', '--input-cursor=no', '--cursor-autohide=no', '--taskbar-progress=no',
                f'--input-ipc-server={self.pipe}', '--really-quiet', '--no-terminal',
                '--mute=yes', f"--volume={int(cfg.get('volume', 60))}", '--audio-display=no']
        if idx:
            args.append('--aid=no')                            # звук только с основного монитора
        self.proc = subprocess.Popen(args, creationflags=NO_WINDOW)
        job.add(self.proc.pid)
        self.state['mute'] = True
        log('mpv', idx, 'pid', self.proc.pid, video, mon)

    def alive(self):
        return self.proc.poll() is None and bool(self.hwnd) and bool(u32.IsWindow(self.hwnd))

    def attach(self, host, below):
        """Проверить, что видео на месте: в нужном окне рабочего стола, под ярлыками и над слоем WorkerW.
        False — рабочий стол пересоздан (перезапуск Проводника), плеер надо запустить заново."""
        if host != self.parent or u32.GetParent(self.hwnd) != host:
            return False
        if misplaced(host, self.hwnd, below):
            u32.SetWindowPos(self.hwnd, below or None, 0, 0, 0, 0, SWP_NOACTIVATE | 0x1 | 0x2)  # NOSIZE|NOMOVE
            log('видео возвращено под ярлыки', self.idx)
        return True

    def command(self, *cmd):
        try:
            with open(self.pipe, 'r+b', buffering=0) as p:
                p.write((json.dumps({'command': list(cmd)}) + '\n').encode())
            return True
        except OSError:
            return False

    def load(self, video):
        """Сменить ролик в том же окне: без мелькания и без повторного встраивания."""
        if self.command('loadfile', video, 'replace'):
            self.video = video
            log('mpv', self.idx, 'новый ролик', video)
            return True
        return False

    def set(self, prop, value):
        if self.state.get(prop) == value:
            return
        try:
            with open(self.pipe, 'r+b', buffering=0) as p:
                p.write((json.dumps({'command': ['set_property', prop, value]}) + '\n').encode())
            self.state[prop] = value
        except OSError:
            pass                                               # mpv ещё не открыл pipe — повторим в следующий раз

    def stop(self):
        if self.proc.poll() is None:
            self.proc.kill()
        if self.hwnd and u32.IsWindow(self.hwnd):
            u32.DestroyWindow(self.hwnd)


def set_static_wallpaper(image):
    """Обычная картинка рабочего стола (кадр из ролика): видна, пока движок запускается, и на других экранах Windows."""
    if image and os.path.exists(image):
        buf = ctypes.create_unicode_buffer(image)
        u32.SystemParametersInfoW(0x14, 0, buf, 0x1 | 0x2)     # SPI_SETDESKWALLPAPER, сохранить и разослать


def refresh_desktop():
    """После остановки обоев перерисовать обычную картинку рабочего стола."""
    buf = ctypes.create_unicode_buffer(520)
    u32.SystemParametersInfoW(0x73, 520, buf, 0)               # SPI_GETDESKWALLPAPER
    u32.SystemParametersInfoW(0x14, 0, buf, 0x2)


def fullscreen_monitor(fg, mons):
    """Индекс монитора, который целиком закрыт полноэкранным окном (игра, видео), иначе None."""
    if not fg or cls(fg) in SHELL_CLASSES:
        return None
    # развёрнутое окно с заголовком (браузер, терминал) — не полноэкранный режим, обои не останавливаем
    if u32.IsZoomed(fg) or (u32.GetWindowLongPtrW(fg, GWL_STYLE) & WS_CAPTION) == WS_CAPTION:
        return None
    r = rect(fg)
    for i, m in enumerate(mons):
        if r[0] <= m[0] and r[1] <= m[1] and r[2] >= m[2] and r[3] >= m[3]:
            return i
    return None


def read_config():
    """Настройки или None, если config.json сейчас недочитан/повреждён (тогда оставляем прежние)."""
    try:
        with open(CONFIG, encoding='utf-8-sig') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except (OSError, ValueError):
        return None
    cfg = load_config()
    cfg.update(data)
    return cfg


def video_for(cfg):
    cur = cfg.get('current')
    if not cur:
        return None
    for ext in ('mkv', 'mp4', 'webm'):
        p = os.path.join(VIDEO_DIR, f'{cur}.{ext}')
        if os.path.exists(p):
            return p
    return None


def running():
    """Запущен ли уже движок (для лаунчера)."""
    h = k32.OpenMutexW(0x00100000, False, MUTEX_NAME)          # SYNCHRONIZE
    if h:
        k32.CloseHandle(h)
        return True
    return False


def mpv_ok():
    return os.path.isabs(tool('mpv')) or bool(__import__('shutil').which('mpv'))


def start(app_dir=None):
    """Запустить движок отдельным фоновым процессом (если ещё не запущен)."""
    if running():
        return
    if FROZEN or app_dir:
        exe = os.path.join(app_dir or APP_DIR, 'MimiWallpapers.exe')
        args = [exe, '--engine']
    else:
        args = [sys.executable.replace('python.exe', 'pythonw.exe'), os.path.abspath(__file__)]
    subprocess.Popen(args, cwd=os.path.dirname(args[0]) if FROZEN or app_dir else APP_DIR,
                     creationflags=NO_WINDOW | 0x00000008)    # DETACHED_PROCESS: живёт и после закрытия лаунчера


def close_lively():
    """Lively Wallpaper рисует свои обои в то же место рабочего стола — два движка мешают друг другу."""
    r = subprocess.run(['taskkill', '/f', '/im', 'Lively.exe'], capture_output=True, creationflags=NO_WINDOW)
    if r.returncode == 0:
        log('Lively Wallpaper закрыта: обои теперь показывает Mimi Wallpapers')


def foreign_wallpaper(host, our_windows):
    """Встроил ли кто-то ещё (Lively) своё окно в рабочий стол — например, если Lively стартовала после нас."""
    c = u32.FindWindowExW(host, None, None, None)
    while c:
        if cls(c) not in ('SHELLDLL_DefView', 'WorkerW', HOST_CLASS) and c not in our_windows:
            return True
        c = u32.FindWindowExW(host, c, None, None)
    return False


def desktop_picture(video):
    """Кадр ролика как обычная картинка рабочего стола: видна при загрузке Windows, пока движок не запустился."""
    try:
        out = os.path.join(DATA_DIR, 'desktop_' + os.path.splitext(os.path.basename(video))[0] + '.jpg')
        if not os.path.exists(out):
            subprocess.run([tool('ffmpeg'), '-y', '-v', 'error', '-ss', '3', '-i', video, '-frames:v', '1', '-q:v', '2',
                            out], capture_output=True, timeout=120, creationflags=NO_WINDOW)
        set_static_wallpaper(out)
    except (OSError, subprocess.SubprocessError) as e:
        log('кадр для рабочего стола не получился:', e)


def main():
    try:
        u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # координаты мониторов в настоящих пикселях
    except (AttributeError, OSError):
        pass
    mutex = k32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == 183:                         # ERROR_ALREADY_EXISTS — движок уже работает
        return
    log('движок запущен, pid', os.getpid())
    close_lively()
    job = Job()
    players, video, mons, cfg_mtime, cfg = [], None, [], None, load_config()
    host, below, last_host_check = None, None, 0
    last_fs = None
    try:
        while True:
            try:
                # 1. настройки
                try:
                    mt = os.path.getmtime(CONFIG)
                except OSError:
                    mt = None
                if mt != cfg_mtime:
                    new = read_config()
                    if new is not None:                            # файл пишется прямо сейчас — прочитаем в следующий раз
                        cfg_mtime, cfg = mt, new
                want = video_for(cfg)
                if not want:
                    log('обои выключены — движок завершается')
                    break
                now_mons = monitors()
                # 2. (пере)запуск mpv при смене ролика, мониторов или если mpv закрылся
                if want != video:
                    threading.Thread(target=desktop_picture, args=(want,), daemon=True).start()
                if want != video and players and now_mons == mons and all(p.alive() for p in players) \
                        and all(p.load(want) for p in players):
                    video = want
                # 3. рабочий стол (заново — раз в 5 с и после перезапуска Проводника)
                if host is None or not u32.IsWindow(host) or time.time() - last_host_check > 5:
                    host, below = desktop_host()
                    last_host_check = time.time()
                    if foreign_wallpaper(host, {p.hwnd for p in players}):
                        close_lively()
                restart = any(not p.attach(host, below) for p in players)
                if want != video or now_mons != mons or restart or any(not p.alive() for p in players):
                    for p in players:
                        p.stop()
                    video, mons = want, now_mons
                    players = [Player(i, video, m, cfg, job, host, below) for i, m in enumerate(mons)]
                    log('плееры запущены в', cls(host), hex(host or 0), [hex(p.hwnd or 0) for p in players])
                # 4. звук и пауза
                fg = u32.GetForegroundWindow()
                fg_pid = W.DWORD()
                u32.GetWindowThreadProcessId(fg, ctypes.byref(fg_pid))
                if fg_pid.value in {p.proc.pid for p in players} | {os.getpid()}:
                    fg = None                              # активно окно наших же обоев — это тот же рабочий стол
                on_desktop = (not fg) or cls(fg) in DESKTOP_CLASSES
                sound = bool(cfg.get('sound'))
                everywhere = bool(cfg.get('audio_everywhere'))
                fs = fullscreen_monitor(fg, mons)
                if fs != last_fs:
                    log('полноэкранное окно:', f'{cls(fg)} {rect(fg)} на мониторе {fs}' if fs is not None else 'нет')
                    last_fs = fs
                for p in players:
                    if p.idx == 0:
                        p.set('volume', int(cfg.get('volume', 60)))
                        p.set('mute', not (sound and (everywhere or on_desktop)))
                    # полноэкранная игра/видео на этом мониторе — пауза (если не просили звук везде)
                    p.set('pause', fs == p.idx and not (sound and everywhere and p.idx == 0))
            except Exception:                              # сбой одного шага (например, Проводник перезапускается)
                log('ошибка:', traceback.format_exc().strip().splitlines()[-1])
                log(traceback.format_exc())
                host = None
                time.sleep(1)
            pump(0.5)
    finally:
        for p in players:
            p.stop()
        refresh_desktop()
        k32.CloseHandle(mutex)
        log('движок остановлен')


if __name__ == '__main__':
    main()
