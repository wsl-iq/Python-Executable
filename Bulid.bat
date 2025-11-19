@echo off
title Building PyToExe EXE...
cls

echo ========================================
echo   Building PyToExe with PyInstaller
echo   Using fixed runtime temp directory
echo ========================================
echo.

REM delete old build/dist folders
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q PyToExe.spec 2>nul

REM create runtime directory
set RUNTIME_DIR=%LOCALAPPDATA%\PyToExeRuntime
if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"

echo Runtime directory:
echo %RUNTIME_DIR%
echo.

pyinstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --name PyToExe ^
    --icon=icons\pytoexe.ico ^
    --runtime-tmpdir "%RUNTIME_DIR%" ^
    PyToExe.py

echo.
echo ======= DONE =======
echo Runtime dir used: %RUNTIME_DIR%
echo Dist folder ready.

pause
