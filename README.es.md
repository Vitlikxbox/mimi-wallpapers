# Mimi Wallpapers

[English](README.md) · [Русский](README.ru.md) · **Español**

Fondos de escritorio animados con **Mimi**, el personaje de las animaciones de **[Typh](https://www.youtube.com/@crispytyph)**.
Proyecto de fans gratuito y sin ánimo de lucro de **MimiFanStudio**.

> **Sin relación con Typh.** Mimi y todas las animaciones © Typh. Este repositorio **no** contiene fotogramas, videos ni dibujos de Typh.
> La aplicación descarga videos del canal oficial de YouTube de Typh en tu equipo **solo para usarlos como fondo personal**.
> Apoya al creador: mira sus videos y dales “me gusta” en YouTube.

## Funciones
- **Catálogo de animaciones de Typh**: los títulos y las miniaturas vienen directamente de YouTube.
- **Solo el canal de Typh**: puedes añadir videos nuevos por enlace, pero solo del canal de Typh. La aplicación comprueba el ID del canal.
- **Descarga en máxima calidad**: hasta 4K a 60 fps con sonido, con [yt-dlp](https://github.com/yt-dlp/yt-dlp). La barra de progreso nunca retrocede.
- **Sin créditos largos**: los créditos del final del video se recortan automáticamente tras la descarga, sin pérdida de calidad.
- **Fondo animado**: un clic pone el video en el escritorio en bucle, con [Lively Wallpaper](https://github.com/rocksdanister/lively) y decodificación por hardware.
- **Pantalla de bloqueo**: eliges un fotograma con un deslizador y se aplica en resolución completa, sin permisos de administrador.
- **Sonido sí/no** y volumen del fondo. Por defecto solo suena en el escritorio vacío; activa **«Sonido en todas partes»** en Ajustes para oírlo en cualquier ventana o pestaña.
- **Iniciar con Windows**: tu último fondo vuelve tras reiniciar.
- **Idiomas**: Español, English, Русский.
- **Instalador con Mimi**: desde el primer segundo muestra una presentación con las miniaturas de los videos de Typh (cargadas desde YouTube), con condiciones de uso. Instala por usuario (sin permisos de administrador) y obtiene las herramientas que falten con `winget`. Se desinstala desde *Aplicaciones*.

## Instalación
1. Descarga `MimiWallpapers_Setup_public.exe` desde [Releases](../../releases).
2. Ejecútalo, elige el idioma, acepta las condiciones y pulsa **Instalar**.
   Si hace falta, el instalador añade Lively Wallpaper, yt-dlp y FFmpeg desde el catálogo oficial `winget` de Windows.
3. Abre **Mimi Wallpapers**, elige un video y pulsa **Descargar** → **Poner de fondo**.

Requisitos: Windows 10/11 x64 y conexión a internet.

> ⚠️ **Los videos se descargan de YouTube.** Si YouTube está bloqueado o ralentizado en tu país, los fondos **no se descargarán sin una VPN** (u otra forma de acceder a YouTube). Los fondos ya descargados siguen funcionando sin conexión.

## Compilar desde el código
```powershell
python -m venv .venv
.venv\Scripts\pip install PySide6-Essentials pyinstaller pywinauto pillow
powershell -ExecutionPolicy Bypass -File build.ps1 -Public
```
El instalador queda en `installer\MimiWallpapers_Setup_public.exe`.

Sin `-Public`, la compilación puede incluir archivos de diseño personales (`launcher_bg.mp4`, `setup_bg.webp`, `mimi.ico`, `mimi.png`) si los creaste tú a partir de tus descargas. Git los ignora y **no se deben publicar**.

## Estructura
| Ruta | Qué es |
|---|---|
| `launcher/mimi_launcher.py` | el lanzador (Python + PySide6) |
| `launcher/setup.py` | el instalador |
| `launcher/common.py` | rutas comunes, estilo, fondo animado |
| `launcher/i18n.py` | traducciones, condiciones de uso, ID del canal de Typh |
| `catalog.json` | catálogo de videos (ID de YouTube y títulos) |
| `tools/make_public_assets.py` | genera el icono y el fondo animado al compilar |
| `tests/` | pruebas de interfaz (pywinauto): lanzador, instalación, desinstalación |
| `build.ps1` | script de compilación |

## Pruebas
```powershell
.venv\Scripts\python tests\ui_test_launcher.py   # 15 comprobaciones
.venv\Scripts\python tests\ui_test_setup.py      # 17 comprobaciones
.venv\Scripts\python tests\ui_test_sound.py      # 5 comprobaciones
```

## Condiciones y licencia
- [Condiciones de uso](TERMS.md#español) (también se muestran en el instalador y en la aplicación).
- Código fuente: [MIT](LICENSE) © 2026 MimiFanStudio.
- Mimi y las animaciones: © Typh. No se incluyen ni se licencian aquí.
- Software de terceros: Lively Wallpaper (GPL-3.0), yt-dlp (Unlicense), FFmpeg (LGPL/GPL), Qt for Python / PySide6 (LGPL-3.0).
