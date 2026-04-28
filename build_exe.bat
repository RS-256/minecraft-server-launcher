@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%dist"

if not "%~1"=="" (
    set "OUTPUT_DIR=%~1"
)

cd /d "%PROJECT_ROOT%"

echo Building executable...
echo Output folder: "%OUTPUT_DIR%"

python -m PyInstaller --clean --distpath "%OUTPUT_DIR%" --workpath "%PROJECT_ROOT%build" main.spec

if errorlevel 1 (
    echo.
    echo Build failed.
    exit /b 1
)

echo.
echo Build complete.
echo Executable: "%OUTPUT_DIR%\minecraft_server_launcher.exe"
