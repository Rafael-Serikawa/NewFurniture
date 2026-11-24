#!/usr/bin/env bash
# Instalação inicial do NewFurniture (Linux/macOS)
set -e
cd "$(dirname "$0")"

echo "==> Backend (Django)"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py popular_dados
deactivate
cd ..

echo "==> Frontend (React + Vite)"
cd frontend
npm install
cd ..

echo ""
echo "Pronto! Agora rode ./iniciar.sh e abra http://localhost:5173"
echo "Contas de demonstração: ana@cliente.com, carla@designer.com, eduardo@marceneiro.com (senha: senha123)"
