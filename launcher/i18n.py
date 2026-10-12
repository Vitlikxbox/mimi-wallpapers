"""Переводы Mimi Wallpapers: русский, английский, испанский. Общие для лаунчера и установщика."""

LANGS = {'ru': 'Русский', 'en': 'English', 'es': 'Español'}
COMPANY = 'MimiFanStudio'
VERSION = '1.2'
TYPH_CHANNEL_ID = 'UCdARcqAEmGmU9ppAx8KHiVQ'      # канал Typh на YouTube (@crispytyph)
TYPH_HANDLE = '@crispytyph'

T = {
    # --- лаунчер
    'subtitle': {'ru': 'живые обои с Mimi · анимации Typh', 'en': 'live wallpapers with Mimi · animations by Typh',
                 'es': 'fondos animados con Mimi · animaciones de Typh'},
    'autostart': {'ru': 'запускать с Windows', 'en': 'start with Windows', 'es': 'iniciar con Windows'},
    'sound_on': {'ru': '🔊  Звук: вкл', 'en': '🔊  Sound: on', 'es': '🔊  Sonido: sí'},
    'sound_off': {'ru': '🔇  Звук: выкл', 'en': '🔇  Sound: off', 'es': '🔇  Sonido: no'},
    'settings': {'ru': '⚙  Настройки', 'en': '⚙  Settings', 'es': '⚙  Ajustes'},
    'url_hint': {'ru': 'Ссылка на ролик Typh с YouTube…', 'en': 'Link to a Typh video on YouTube…',
                 'es': 'Enlace a un video de Typh en YouTube…'},
    'add': {'ru': 'Добавить', 'en': 'Add', 'es': 'Añadir'},
    'downloaded': {'ru': '✔ скачано', 'en': '✔ downloaded', 'es': '✔ descargado'},
    'not_downloaded': {'ru': '⬇ не скачано', 'en': '⬇ not downloaded', 'es': '⬇ no descargado'},
    'on_wallpaper': {'ru': '★ на обоях', 'en': '★ on desktop', 'es': '★ en el escritorio'},
    'sec': {'ru': 'с', 'en': 's', 'es': 's'},
    'author': {'ru': 'Автор', 'en': 'Author', 'es': 'Autor'},
    'file': {'ru': 'Файл', 'en': 'File', 'es': 'Archivo'},
    'not_yet': {'ru': 'Ещё не скачано', 'en': 'Not downloaded yet', 'es': 'Aún no descargado'},
    'btn_download': {'ru': '⬇  Скачать (лучшее качество)', 'en': '⬇  Download (best quality)',
                     'es': '⬇  Descargar (máxima calidad)'},
    'btn_apply': {'ru': '🖥  Поставить на обои', 'en': '🖥  Set as wallpaper', 'es': '🖥  Poner de fondo'},
    'btn_lock': {'ru': '🔒  На экран блокировки', 'en': '🔒  Set on lock screen', 'es': '🔒  Poner en bloqueo'},
    'btn_delete': {'ru': 'Удалить видео', 'en': 'Delete video', 'es': 'Borrar video'},
    'note': {'ru': 'Видео скачиваются только для ваших обоев. Анимации © Typh.',
             'en': 'Videos are downloaded for your own wallpaper only. Animations © Typh.',
             'es': 'Los videos se descargan solo para tu fondo. Animaciones © Typh.'},
    'legal_link': {'ru': 'Авторские права и условия', 'en': 'Copyright & terms', 'es': 'Derechos y condiciones'},
    'no_lively': {'ru': 'Не найдена Lively Wallpaper — без неё обои не применятся. Переустановите Mimi Wallpapers.',
                  'en': 'Lively Wallpaper was not found — wallpapers cannot be applied. Please reinstall Mimi Wallpapers.',
                  'es': 'No se encontró Lively Wallpaper: no se pueden aplicar fondos. Reinstala Mimi Wallpapers.'},
    'bad_link': {'ru': 'Не похоже на ссылку YouTube.', 'en': 'This does not look like a YouTube link.',
                 'es': 'No parece un enlace de YouTube.'},
    'already': {'ru': 'Этот ролик уже есть в каталоге.', 'en': 'This video is already in the catalog.',
                'es': 'Este video ya está en el catálogo.'},
    'checking': {'ru': 'Проверяю ролик…', 'en': 'Checking the video…', 'es': 'Comprobando el video…'},
    'no_info': {'ru': 'Не удалось получить данные ролика.', 'en': 'Could not get video info.',
                'es': 'No se pudo obtener la información del video.'},
    'only_typh': {'ru': 'Можно добавлять только ролики с канала Typh (' + TYPH_HANDLE + '). Этот ролик загружен каналом «{ch}».',
                  'en': 'Only videos from the Typh channel (' + TYPH_HANDLE + ') can be added. This one is from “{ch}”.',
                  'es': 'Solo se pueden añadir videos del canal de Typh (' + TYPH_HANDLE + '). Este es de «{ch}».'},
    'added': {'ru': 'Добавлено: {t}', 'en': 'Added: {t}', 'es': 'Añadido: {t}'},
    'dl_video': {'ru': 'Скачиваю видео…', 'en': 'Downloading video…', 'es': 'Descargando video…'},
    'dl_audio': {'ru': 'Скачиваю звук…', 'en': 'Downloading audio…', 'es': 'Descargando audio…'},
    'dl_merge': {'ru': 'Склеиваю видео и звук…', 'en': 'Merging video and audio…', 'es': 'Uniendo video y audio…'},
    'dl_preview': {'ru': 'Готовлю превью…', 'en': 'Preparing preview…', 'es': 'Preparando vista previa…'},
    'dl_done': {'ru': 'Скачано. Можно ставить на обои.', 'en': 'Downloaded. Ready to set as wallpaper.',
                'es': 'Descargado. Listo para poner de fondo.'},
    'dl_fail': {'ru': 'Не удалось скачать. Проверьте интернет и попробуйте ещё раз.',
                'en': 'Download failed. Check your internet connection and try again.',
                'es': 'Error de descarga. Revisa tu conexión e inténtalo de nuevo.'},
    'applied': {'ru': 'Обои установлены и крутятся по кругу.', 'en': 'Wallpaper set and looping.',
                'es': 'Fondo aplicado en bucle.'},
    'frame_cut': {'ru': 'Вырезаю кадр в полном качестве…', 'en': 'Extracting the frame in full quality…',
                  'es': 'Extrayendo el fotograma en calidad completa…'},
    'frame_fail': {'ru': 'Не удалось вырезать кадр.', 'en': 'Could not extract the frame.',
                   'es': 'No se pudo extraer el fotograma.'},
    'lock_ok': {'ru': 'Экран блокировки обновлён (Win + L, чтобы посмотреть).',
                'en': 'Lock screen updated (press Win + L to see it).',
                'es': 'Pantalla de bloqueo actualizada (Win + L para verla).'},
    'lock_fail': {'ru': 'Windows не дала сменить экран блокировки.', 'en': 'Windows refused to change the lock screen.',
                  'es': 'Windows no permitió cambiar la pantalla de bloqueo.'},
    'delete_q': {'ru': 'Удалить скачанное видео?', 'en': 'Delete the downloaded video?',
                 'es': '¿Borrar el video descargado?'},
    'deleted': {'ru': 'Видео удалено.', 'en': 'Video deleted.', 'es': 'Video borrado.'},
    'frame_title': {'ru': 'Кадр для экрана блокировки', 'en': 'Lock screen frame', 'es': 'Fotograma para el bloqueo'},
    'frame_ok': {'ru': '🔒  Поставить этот кадр', 'en': '🔒  Use this frame', 'es': '🔒  Usar este fotograma'},
    'of': {'ru': 'из', 'en': 'of', 'es': 'de'},
    'audio_everywhere': {'ru': 'Звук везде: и в окнах, и во вкладках (по умолчанию — только на рабочем столе)',
                         'en': 'Sound everywhere: in windows and tabs too (default: desktop only)',
                         'es': 'Sonido en todas partes: también en ventanas y pestañas (por defecto: solo en el escritorio)'},
    'sound_setup': {'ru': 'Настраиваю звук в Lively…', 'en': 'Setting up sound in Lively…',
                    'es': 'Configurando el sonido en Lively…'},
    'language': {'ru': 'Язык', 'en': 'Language', 'es': 'Idioma'},
    'volume': {'ru': 'Громкость обоев', 'en': 'Wallpaper volume', 'es': 'Volumen del fondo'},
    'restart_lang': {'ru': 'Лаунчер перезапустится на выбранном языке.', 'en': 'The launcher will restart in the selected language.',
                     'es': 'El lanzador se reiniciará en el idioma elegido.'},
    'save': {'ru': 'Сохранить', 'en': 'Save', 'es': 'Guardar'},
    'close': {'ru': 'Закрыть', 'en': 'Close', 'es': 'Cerrar'},
    'uninstall': {'ru': 'Удалить Mimi Wallpapers', 'en': 'Uninstall Mimi Wallpapers', 'es': 'Desinstalar Mimi Wallpapers'},
    'uninstall_q': {'ru': 'Удалить Mimi Wallpapers с компьютера?', 'en': 'Remove Mimi Wallpapers from this computer?',
                    'es': '¿Quitar Mimi Wallpapers de este equipo?'},
    'uninstall_data_q': {'ru': 'Удалить и скачанные видео?', 'en': 'Also delete downloaded videos?',
                         'es': '¿Borrar también los videos descargados?'},
    'uninstall_done': {'ru': 'Mimi Wallpapers удалён.', 'en': 'Mimi Wallpapers has been removed.',
                       'es': 'Mimi Wallpapers se ha desinstalado.'},
    # --- установщик
    'setup_title': {'ru': 'Установка Mimi Wallpapers', 'en': 'Mimi Wallpapers Setup', 'es': 'Instalación de Mimi Wallpapers'},
    'choose_lang': {'ru': 'Выберите язык', 'en': 'Choose your language', 'es': 'Elige tu idioma'},
    'welcome': {'ru': 'Добро пожаловать!', 'en': 'Welcome!', 'es': '¡Bienvenido!'},
    'welcome_text': {'ru': 'Mimi Wallpapers ставит на рабочий стол живые обои с Mimi из анимаций Typh. Прочитайте условия использования.',
                     'en': 'Mimi Wallpapers puts live wallpapers with Mimi from Typh’s animations on your desktop. Please read the terms of use.',
                     'es': 'Mimi Wallpapers pone en tu escritorio fondos animados con Mimi de las animaciones de Typh. Lee las condiciones de uso.'},
    'accept': {'ru': 'Я принимаю условия использования', 'en': 'I accept the terms of use', 'es': 'Acepto las condiciones de uso'},
    'next': {'ru': 'Далее  →', 'en': 'Next  →', 'es': 'Siguiente  →'},
    'back': {'ru': '←  Назад', 'en': '←  Back', 'es': '←  Atrás'},
    'install': {'ru': 'Установить', 'en': 'Install', 'es': 'Instalar'},
    'folder': {'ru': 'Папка установки', 'en': 'Install folder', 'es': 'Carpeta de instalación'},
    'browse': {'ru': 'Обзор…', 'en': 'Browse…', 'es': 'Examinar…'},
    'opt_desktop': {'ru': 'Ярлык на рабочем столе', 'en': 'Desktop shortcut', 'es': 'Acceso directo en el escritorio'},
    'opt_startmenu': {'ru': 'Ярлык в меню «Пуск»', 'en': 'Start menu shortcut', 'es': 'Acceso en el menú Inicio'},
    'opt_autostart': {'ru': 'Запускать обои вместе с Windows', 'en': 'Start wallpapers with Windows',
                      'es': 'Iniciar los fondos con Windows'},
    'opt_deps': {'ru': 'Установить нужные программы (Lively Wallpaper, yt-dlp, ffmpeg), если их нет',
                 'en': 'Install required programs (Lively Wallpaper, yt-dlp, ffmpeg) if missing',
                 'es': 'Instalar los programas necesarios (Lively Wallpaper, yt-dlp, ffmpeg) si faltan'},
    'installing': {'ru': 'Устанавливаю…', 'en': 'Installing…', 'es': 'Instalando…'},
    'st_files': {'ru': 'Копирую файлы…', 'en': 'Copying files…', 'es': 'Copiando archivos…'},
    'st_shortcuts': {'ru': 'Создаю ярлыки…', 'en': 'Creating shortcuts…', 'es': 'Creando accesos directos…'},
    'st_register': {'ru': 'Регистрирую программу…', 'en': 'Registering the app…', 'es': 'Registrando la aplicación…'},
    'st_dep': {'ru': 'Устанавливаю {n}…', 'en': 'Installing {n}…', 'es': 'Instalando {n}…'},
    'st_dep_ok': {'ru': '{n} уже есть', 'en': '{n} already installed', 'es': '{n} ya está instalado'},
    'done_title': {'ru': 'Готово!', 'en': 'All done!', 'es': '¡Listo!'},
    'done_text': {'ru': 'Mimi Wallpapers установлен. Выберите ролик, скачайте его и поставьте на обои.',
                  'en': 'Mimi Wallpapers is installed. Pick a video, download it and set it as your wallpaper.',
                  'es': 'Mimi Wallpapers está instalado. Elige un video, descárgalo y ponlo de fondo.'},
    'launch': {'ru': 'Запустить Mimi Wallpapers', 'en': 'Launch Mimi Wallpapers', 'es': 'Abrir Mimi Wallpapers'},
    'finish': {'ru': 'Готово', 'en': 'Finish', 'es': 'Finalizar'},
    'error': {'ru': 'Ошибка установки', 'en': 'Setup error', 'es': 'Error de instalación'},
    'legal_title': {'ru': 'Авторские права и условия использования', 'en': 'Copyright and terms of use',
                    'es': 'Derechos de autor y condiciones de uso'},
}

TERMS = {
    'ru': f"""<h3>Условия использования Mimi Wallpapers</h3>
<p><b>{COMPANY}</b> · версия {VERSION}</p>
<p><b>1. Что это.</b> Mimi Wallpapers — бесплатный некоммерческий фанатский проект {COMPANY}. Программа помогает поставить на рабочий стол и экран блокировки обои из анимаций с персонажем Mimi.</p>
<p><b>2. Авторские права на анимации.</b> Персонаж Mimi и все анимации принадлежат их автору, аниматору <b>Typh</b> (YouTube: {TYPH_HANDLE}). {COMPANY} не связана с Typh, не получала от него одобрения и не претендует на какие-либо права на его работы. Каталог ограничен роликами с официального канала Typh.</p>
<p><b>3. Только личное использование.</b> Видео скачиваются на ваш компьютер исключительно как обои для личного некоммерческого использования. Запрещено распространять, выкладывать, продавать скачанные видео или использовать их в коммерческих целях. Пожалуйста, поддерживайте автора: смотрите и лайкайте его ролики на YouTube.</p>
<p><b>4. Ответственность пользователя.</b> Вы самостоятельно отвечаете за соблюдение законов вашей страны и правил YouTube при скачивании видео. Если правообладатель попросит прекратить использование его работ, проект будет изменён или закрыт.</p>
<p><b>5. Сторонние программы.</b> Программа использует Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL) и Qt / PySide6 (LGPL-3.0). Права на них принадлежат их авторам.</p>
<p><b>6. Без гарантий.</b> Программа предоставляется «как есть», без каких-либо гарантий. {COMPANY} не отвечает за возможные убытки, потерю данных или неполадки, связанные с её использованием.</p>
<p><b>7. Данные.</b> Программа не собирает и не отправляет личные данные. Обращения в интернет: YouTube (превью и видео) и каталог программ winget при установке.</p>
<p>Устанавливая или используя программу, вы соглашаетесь с этими условиями.</p>
<p>© 2026 {COMPANY}. Программа Mimi Wallpapers. Анимации и персонаж Mimi © Typh.</p>""",
    'en': f"""<h3>Mimi Wallpapers Terms of Use</h3>
<p><b>{COMPANY}</b> · version {VERSION}</p>
<p><b>1. What it is.</b> Mimi Wallpapers is a free, non-commercial fan project by {COMPANY}. It helps you set wallpapers made from animations featuring the character Mimi on your desktop and lock screen.</p>
<p><b>2. Copyright of the animations.</b> The character Mimi and all animations belong to their creator, the animator <b>Typh</b> (YouTube: {TYPH_HANDLE}). {COMPANY} is not affiliated with or endorsed by Typh and claims no rights to Typh’s works. The catalog is limited to videos from Typh’s official channel.</p>
<p><b>3. Personal use only.</b> Videos are downloaded to your computer solely as wallpapers for personal, non-commercial use. You may not redistribute, upload, sell or commercially use downloaded videos. Please support the creator by watching and liking the videos on YouTube.</p>
<p><b>4. Your responsibility.</b> You are responsible for complying with the laws of your country and YouTube’s terms when downloading videos. If the rights holder asks us to stop using their works, the project will be changed or discontinued.</p>
<p><b>5. Third-party software.</b> The app uses Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL) and Qt / PySide6 (LGPL-3.0). These belong to their respective authors.</p>
<p><b>6. No warranty.</b> The software is provided “as is”, without warranty of any kind. {COMPANY} is not liable for any damage, data loss or malfunction arising from its use.</p>
<p><b>7. Data.</b> The app does not collect or send personal data. Network access: YouTube (thumbnails and videos) and the winget catalog during setup.</p>
<p>By installing or using the app you agree to these terms.</p>
<p>© 2026 {COMPANY}. Mimi Wallpapers software. Animations and the character Mimi © Typh.</p>""",
    'es': f"""<h3>Condiciones de uso de Mimi Wallpapers</h3>
<p><b>{COMPANY}</b> · versión {VERSION}</p>
<p><b>1. Qué es.</b> Mimi Wallpapers es un proyecto de fans gratuito y sin ánimo de lucro de {COMPANY}. Te ayuda a poner en el escritorio y en la pantalla de bloqueo fondos hechos con animaciones del personaje Mimi.</p>
<p><b>2. Derechos de autor de las animaciones.</b> El personaje Mimi y todas las animaciones pertenecen a su creador, el animador <b>Typh</b> (YouTube: {TYPH_HANDLE}). {COMPANY} no está afiliada ni respaldada por Typh y no reclama ningún derecho sobre sus obras. El catálogo se limita a videos del canal oficial de Typh.</p>
<p><b>3. Solo uso personal.</b> Los videos se descargan en tu equipo únicamente como fondos para uso personal y no comercial. No está permitido redistribuir, subir, vender ni usar comercialmente los videos descargados. Apoya al creador viendo y dando “me gusta” a sus videos en YouTube.</p>
<p><b>4. Tu responsabilidad.</b> Eres responsable de cumplir las leyes de tu país y las condiciones de YouTube al descargar videos. Si el titular de los derechos pide dejar de usar sus obras, el proyecto se modificará o se cerrará.</p>
<p><b>5. Software de terceros.</b> La aplicación usa Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL) y Qt / PySide6 (LGPL-3.0). Pertenecen a sus respectivos autores.</p>
<p><b>6. Sin garantía.</b> El software se ofrece “tal cual”, sin garantía de ningún tipo. {COMPANY} no se hace responsable de daños, pérdida de datos o fallos derivados de su uso.</p>
<p><b>7. Datos.</b> La aplicación no recopila ni envía datos personales. Acceso a internet: YouTube (miniaturas y videos) y el catálogo winget durante la instalación.</p>
<p>Al instalar o usar la aplicación aceptas estas condiciones.</p>
<p>© 2026 {COMPANY}. Software Mimi Wallpapers. Animaciones y personaje Mimi © Typh.</p>""",
}


def tr(key, lang, **kw):
    s = T.get(key, {}).get(lang) or T.get(key, {}).get('en') or key
    return s.format(**kw) if kw else s
