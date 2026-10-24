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
- `backend/catalogo/`: usuarios, invitaciones, catalogos, productos e historial de versiones.
- `docker-compose.yml`: servicio PostgreSQL persistente.

El endpoint de salud confirma la conexion con la base de datos.

## Modelo de datos

La app Django `catalogo` usa un unico usuario autenticable con rol `admin`, `operador` o `cliente`. Un catalogo pertenece a un cliente, tiene un operador creador y puede asignarse a varios operadores; contiene productos e historial de versiones. El diagrama entidad-relacion esta en [docs/diagrama-relaciones.svg](./docs/diagrama-relaciones.svg).

Para crear el primer administrador, inicializar las tablas y arrancar:

```sh
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El superusuario inicial tiene rol `admin`. Desde una sesion autenticada como admin, la API permite invitar operadores o clientes:

```http
POST /api/auth/invitations/
Content-Type: application/json

{"email":"persona@example.com","nombre":"Nombre","apellidos":"Apellido","rol":"operador"}
```

El correo incluye un enlace de un solo uso que vence en 48 horas. El invitado establece una contraseña de al menos 12 caracteres en Vue; luego inicia sesion con su correo. En desarrollo, Django imprime el correo en la consola del backend.

La API usa sesiones y proteccion CSRF: el cliente debe solicitar primero `GET /api/auth/csrf/` y enviar la cookie `csrftoken` tambien como cabecera `X-CSRFToken` en solicitudes de escritura. Rutas disponibles:

- `POST /api/auth/login/`, `POST /api/auth/logout/` y `GET /api/auth/me/`.
- `POST /api/auth/invitations/` (solo admin) y `POST /api/auth/invitations/accept/`.

Para enviar invitaciones fuera de desarrollo, configura SMTP mediante `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` y `DEFAULT_FROM_EMAIL`. Configura `INVITATION_FRONTEND_URL` con la URL publica de Vue. Para permitir el frontend en la API, ajusta `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`.

Si ya ejecutaste una migracion previa del esquema antiguo en una base de datos persistente, no apliques esta migracion inicial recreada sobre esas tablas; se requiere una migracion de datos acorde a esa base. El esquema nuevo debe inicializarse en una base vacia.
