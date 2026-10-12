# Сборка Mimi Wallpapers: лаунчер (папка) → payload.zip → установщик одним exe.
#   .\build.ps1          — личная сборка (с оформлением из анимаций Typh, если файлы есть рядом; НЕ для публикации)
#   .\build.ps1 -Public  — публичная сборка: только своя графика из assets/ (для GitHub Releases)
param([switch]$Public)
$ErrorActionPreference = 'Stop'
$R  = $PSScriptRoot
$PI = "$R\.venv\Scripts\pyinstaller.exe"
New-Item -ItemType Directory -Force "$R\.tmp" | Out-Null
$env:TMP = "$R\.tmp"; $env:TEMP = $env:TMP
# своя графика (иконка, анимированный фон) создаётся здесь: картинок в репозитории нет
if (-not (Test-Path "$R\assets\bg_public.webp")) { & "$R\.venv\Scripts\python.exe" "$R\tools\make_public_assets.py" }
$private = @('launcher_bg.mp4', 'setup_bg.webp', 'mimi.ico', 'mimi.png') | Where-Object { -not $Public -and (Test-Path "$R\$_") }
$icon = if ($private -contains 'mimi.ico') { "$R\mimi.ico" } else { "$R\assets\icon.ico" }
$name = if ($Public) { 'MimiWallpapers_Setup_public' } else { 'MimiWallpapers_Setup' }
$common = @('--noconfirm', '--windowed', '--icon', $icon, '--workpath', "$R\build\work", '--specpath', "$R\build",
            '--paths', "$R\launcher", '--exclude-module', 'PySide6.QtNetwork', '--exclude-module', 'PySide6.QtQml',
            '--exclude-module', 'PySide6.QtQuick', '--exclude-module', 'PySide6.QtMultimedia')

Get-Process MimiWallpapers, MimiWallpapers_Setup* -ErrorAction SilentlyContinue | Stop-Process -Force

# 1. лаунчер
& $PI @common --name MimiWallpapers --distpath "$R\build\dist" "$R\launcher\mimi_launcher.py"
$app = "$R\build\dist\MimiWallpapers"
Copy-Item "$R\catalog.json", "$R\assets\bg_public.webp", "$R\assets\icon.ico", "$R\assets\icon.png" $app -Force
foreach ($f in 'launcher_bg.mp4', 'mimi.ico', 'mimi.png') { if ($private -contains $f) { Copy-Item "$R\$f" $app -Force } else { Remove-Item "$app\$f" -ErrorAction SilentlyContinue } }

# 2. архив программы
$zip = "$R\build\payload.zip"
if (Test-Path $zip) { Remove-Item $zip }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($app, $zip, [IO.Compression.CompressionLevel]::Optimal, $false)

# 3. установщик (один exe)
$data = @('--add-data', "$zip;.", '--add-data', "$R\assets\bg_public.webp;.", '--add-data', "$R\assets\icon.ico;.", '--add-data', "$R\assets\icon.png;.")
foreach ($f in 'setup_bg.webp', 'mimi.ico', 'mimi.png') { if ($private -contains $f) { $data += @('--add-data', "$R\$f;.") } }
# личная сборка: первый ролик вшивается в установщик (сразу на обои, без скачивания и VPN). В публичную — нельзя.
$first = (Get-Content "$R\catalog.json" -Raw | ConvertFrom-Json)[0].id
$vdir = "$env:LOCALAPPDATA\MimiWallpapers\videos"
if (-not $Public -and (Test-Path "$vdir\$first.mkv")) {
    $data += @('--add-data', "$vdir\$first.mkv;.")
    if (Test-Path "$vdir\${first}_preview.mp4") { $data += @('--add-data', "$vdir\${first}_preview.mp4;.") }
}
$data += @('--add-data', "$R\catalog.json;.")
& $PI @common --onefile --name $name --distpath "$R\installer" @data "$R\launcher\setup.py"

Get-ChildItem "$R\installer\$name.exe" | Select-Object Name, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } }
