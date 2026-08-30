@echo off
REM Double-click this on a Windows PC to build Cauldron Company into an .exe.
REM PyInstaller cannot cross-compile, so the Windows build has to happen here.

echo ============================================
echo   Cauldron Company - Windows build
echo ============================================
echo.

REM Find Python. The py launcher is the normal install, plain python is the
REM Microsoft Store one. Checked at top level because %errorlevel% inside a
REM parenthesised block expands too early to be trusted.
set "PYCMD="
py -3 --version >nul 2>&1
if %errorlevel%==0 set "PYCMD=py -3"
python --version >nul 2>&1
if %errorlevel%==0 if not defined PYCMD set "PYCMD=python"
if not defined PYCMD goto :nopython

echo Using: %PYCMD%
%PYCMD% --version
echo.

echo [1/4] Creating a virtual environment...
%PYCMD% -m venv .venv || goto :fail

echo [2/4] Activating it...
call .venv\Scripts\activate.bat || goto :fail

echo [3/4] Installing dependencies (this downloads ~100 MB, be patient)...
python -m pip install --upgrade pip || goto :fail
pip install -r requirements.txt || goto :fail

echo [4/4] Building the executable...
python build_exe.py || goto :fail

echo.
echo ============================================
echo   Done.
echo.
echo   Play it:  dist\CauldronCompany\CauldronCompany.exe
echo.
echo   To share it, zip the WHOLE folder:
echo       dist\CauldronCompany
echo   Not just the .exe - it needs the files next to it.
echo ============================================
pause
exit /b 0

:nopython
echo.
echo Python was not found.
echo.
echo Install Python 3.11 or newer from https://www.python.org/downloads/
echo IMPORTANT: tick "Add python.exe to PATH" on the first install screen.
echo Then run this file again.
pause
exit /b 1

:fail
echo.
echo Build failed. The error is in the text above this line.
pause
exit /b 1
