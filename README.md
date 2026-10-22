# KCR

Base full-stack con Vue 3, Django REST Framework y PostgreSQL.

## Requisitos

- Python 3.12+
- Node.js 20+
- Docker Compose

## Configuracion

1. Copia `.env.example` a `.env` y ajusta los valores.
2. Inicia PostgreSQL: `docker compose up -d db`.
3. Prepara el backend:

   ```sh
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. En otra terminal, inicia Vue:

   ```sh
   cd frontend
   npm install
   npm run dev
   ```

Vue queda disponible en `http://localhost:5173` y la API en `http://localhost:8000/api/health/`.

## Estructura

- `frontend/`: aplicacion Vue 3 y servidor Vite.
- `backend/`: proyecto Django y API REST.
- `docker-compose.yml`: servicio PostgreSQL persistente.

El endpoint de salud confirma la conexion con la base de datos.
