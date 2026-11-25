#!/usr/bin/env bash
# Build do NewFurniture no Render: instala tudo, compila o React e prepara o banco.
set -o errexit

pip install -r backend/requirements.txt

cd frontend
npm install
npm run build
cd ..

cd backend
python manage.py collectstatic --no-input
python manage.py makemigrations core
python manage.py migrate
python manage.py popular_dados
