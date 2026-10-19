@echo off
cd /d "%~dp0"
echo ===== BAJALO: construyendo la app =====

if not exist bin mkdir bin

if not exist bin\ffmpeg.exe (
  echo Descargando FFmpeg ^(unos 200 MB, puede tardar^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile ffmpeg.zip; Expand-Archive ffmpeg.zip -DestinationPath ffmpeg_tmp -Force; Copy-Item 'ffmpeg_tmp\*\bin\ffmpeg.exe','ffmpeg_tmp\*\bin\ffprobe.exe' bin\; Remove-Item ffmpeg.zip,ffmpeg_tmp -Recurse -Force"
)

if not exist bin\deno.exe (
  echo Descargando Deno ^(necesario para YouTube^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest 'https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip' -OutFile deno.zip; Expand-Archive deno.zip -DestinationPath bin -Force; Remove-Item deno.zip -Force"
)

if not exist bin\ffmpeg.exe goto falta
if not exist bin\ffprobe.exe goto falta
if not exist bin\deno.exe goto falta

echo Instalando dependencias de Python...
python -m pip install -U pyinstaller PySide6 "yt-dlp[default]"
if errorlevel 1 goto error

echo Creando el programa...
python -m PyInstaller --noconfirm --clean --windowed --name Bajalo --icon bajalo.ico --collect-all yt_dlp --collect-all yt_dlp_ejs --add-data "bajalo.png;." --add-data "bin;bin" bajalo.py
if errorlevel 1 goto error

echo.
echo ===== LISTO =====
echo Tu app esta en: dist\Bajalo\Bajalo.exe
echo Siguiente paso: abre bajalo.iss con Inno Setup y pulsa Compilar.
pause
exit /b 0

:falta
echo.
echo ERROR: faltan ffmpeg.exe, ffprobe.exe o deno.exe en la carpeta "bin".
echo Descargalos a mano y colocalos ahi, o revisa tu conexion a internet.
pause
exit /b 1

:error
echo.
echo ERROR: algo fallo. Copia el mensaje de arriba y compartelo.
pause
exit /b 1
