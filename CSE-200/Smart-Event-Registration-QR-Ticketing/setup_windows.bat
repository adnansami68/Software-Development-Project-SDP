@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   EventPass - Windows Setup
echo ==========================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python and enable Add Python to PATH.
  pause
  exit /b 1
)
python -m venv .venv
if errorlevel 1 (
  echo Could not create virtual environment.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto fail
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python setup_env.py
if errorlevel 1 goto fail
python manage.py init-db
if errorlevel 1 goto fail
echo.
echo Setup finished. Next run: create_admin.bat
pause
exit /b 0
:fail
echo Setup failed. Read the error above and try again.
pause
exit /b 1
