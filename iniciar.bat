@echo off
REM Abre o backend (porta 8000) e o frontend (porta 5173) em duas janelas
cd /d "%~dp0"
start "NewFurniture - Backend" cmd /k "cd backend && call .venv\Scripts\activate.bat && python manage.py runserver"
start "NewFurniture - Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 5 >nul
start http://localhost:5173
