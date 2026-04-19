@echo off
setlocal

REM Build standalone Windows executable using PyInstaller
cd /d "%~dp0"

if not exist isolation\Scripts\python.exe (
  echo [ERROR] Python environment not found at isolation\Scripts\python.exe
  echo Activate or create your env, then install dependencies.
  exit /b 1
)

echo [1/3] Installing/refreshing dependencies...
isolation\Scripts\python.exe -m pip install --upgrade pip
isolation\Scripts\python.exe -m pip install -r requirements.txt

echo [2/3] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ImgStego.spec del /f /q ImgStego.spec

echo [3/3] Building executable...
isolation\Scripts\python.exe -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name ImgStego ^
  --onefile ^
  --collect-all customtkinter ^
  --collect-submodules cryptography ^
  --add-data "project_info.html;." ^
  --add-data "assets;assets" ^
  main.py

if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)

echo.
echo Build complete.
echo EXE location: dist\ImgStego.exe
echo.
echo IMPORTANT for email feature:
echo Enter sender Gmail and App Password in the app UI while encoding.

endlocal
