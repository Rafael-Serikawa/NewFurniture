@echo off
REM Instalacao inicial do NewFurniture (Windows)
cd /d "%~dp0"

echo ==^> Backend (Django)
cd backend
py -m venv .venv 2>nul || python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt || goto erro
python manage.py makemigrations core || goto erro
python manage.py migrate || goto erro
python manage.py popular_dados || goto erro
call .venv\Scripts\deactivate.bat
cd ..

echo ==^> Frontend (React + Vite)
cd frontend
call npm install || goto erro
cd ..

echo.
echo Pronto! Agora rode iniciar.bat e abra http://localhost:5173
echo Contas: ana@cliente.com, carla@designer.com, eduardo@marceneiro.com (senha: senha123)
pause
exit /b 0

:erro
echo.
echo Ocorreu um erro. Veja a mensagem acima.
pause
exit /b 1
