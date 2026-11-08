# NewFurniture

Plataforma web para design e produção de **móveis sob medida**, conectando três atores:
**Cliente** (publica a necessidade), **Designer/Arquiteto** (envia o desenho técnico) e
**Marceneiro** (fabrica as peças para automontagem).

Trabalho final de **PMR3304 – Sistemas de Informação (Poli-USP, 2026)** — Grupo E:
Erick Kamada Pesce de Oliveira · Lucas Hideki Toyofuku Turri · Rafael Tadao Mendes Serikawa · Victor Hugo de Ávila Ribeiro.

| Camada | Tecnologia |
|---|---|
| Backend / API | Python, **Django** + **Django REST Framework** |
| Banco de dados | **SQLite** |
| Autenticação | **Token** (`rest_framework.authtoken`) |
| Frontend | **React** (JavaScript) com **Vite**, consumindo a API REST |

## Como rodar

Pré-requisitos: **Python 3.10+** e **Node.js 18+**.

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser        # opcional, para o /admin
python manage.py runserver              # http://127.0.0.1:8000

# Frontend (terminal 2)
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

O Vite repassa `/api` e `/media` para o Django (ver `frontend/vite.config.js`).

> Em desenvolvimento: próximas etapas em branches `feature/*`.
