@echo off
setlocal
cd /d "%~dp0"

set PYTHON_CMD=python
if exist "..\venv\Scripts\python.exe" set PYTHON_CMD=..\venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Running migrations...
%PYTHON_CMD% manage.py migrate
if errorlevel 1 goto :error

echo Starting server...
%PYTHON_CMD% manage.py runserver
exit /b %errorlevel%

:error
echo.
echo Startup failed. Check the error message above.
pause
exit /b 1
