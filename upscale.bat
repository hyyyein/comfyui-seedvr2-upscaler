@echo off
setlocal

set "PYTHON_CMD="
where python >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"

if "%PYTHON_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py"
)

if "%PYTHON_CMD%"=="" (
    echo Python was not found. Install Python or add it to PATH.
    pause
    exit /b 1
)

set /p "NAME=Output filename prefix: "
set /p "COMFYUI_URL=ComfyUI URL (blank: http://localhost:8188): "

if "%COMFYUI_URL%"=="" (
    %PYTHON_CMD% "%~dp0upscale.py" --name "%NAME%"
) else (
    %PYTHON_CMD% "%~dp0upscale.py" --name "%NAME%" --comfyui-url "%COMFYUI_URL%"
)

if errorlevel 1 echo Upscale failed.
pause
