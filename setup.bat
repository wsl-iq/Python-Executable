@echo off
title PyQt6 Uninstall & PyQt5 Install
color 0a
echo +----------------------------------------+
echo |  Remove PyQt6 and Install PyQt5        |
echo +----------------------------------------+
echo.
REM Delete PyQt6
pip uninstall -y PyQt6 PyQt6-sip PyQt6-Qt6
echo.
echo [INFO] PyQt6 has been uninstalled.
echo.
REM Installation PyQt5
pip install PyQt5
pip install pyinstaller
echo.
echo [INFO] PyQt5 has been installed successfully.
echo.
pause
