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

if "%COMFYUI_INPUT_DIR%"=="" (
    set /p "COMFYUI_INPUT_DIR=ComfyUI input directory: "
)

set /p "NAME=Output filename prefix: "
%PYTHON_CMD% "%~dp0upscale.py" --name "%NAME%" --input-dir "%COMFYUI_INPUT_DIR%"

if errorlevel 1 echo Upscale failed.
pause
