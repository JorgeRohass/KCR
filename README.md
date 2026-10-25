# EMPRESA

Base full-stack con Vue 3, Django REST Framework y PostgreSQL.

## Requisitos

- Python 3.12+
- Node.js 20+
- Docker Compose

## Esquema de datos

La app Django `catalogo` define estas tablas:

- `usuario`: identidad común con correo, contraseña almacenada con el hash de Django y rol (`admin`, `operador` o `cliente`).
- `invitacion`: usuario invitado, usuario creador, hash del token, vencimiento y fecha de uso.
- `catalogo`: pertenece a un cliente y registra el usuario que lo creó.
- `catalogo_operador`: relación muchos-a-muchos entre catálogos y operadores.
- `producto`: productos pertenecientes a un catálogo.
- `version_previa_catalogo`: cambios del catálogo y usuario editor.

Los tres roles son valores de `usuario.rol`, no tablas separadas. La estructura de `invitacion` está definida en el esquema, pero aún no hay endpoints para iniciar sesión ni para crear o aceptar invitaciones. La API disponible por ahora es `GET /api/health/`.

## Configuración y ejecución

1. Copia `.env.example` a `.env` en la raíz y ajusta las credenciales de PostgreSQL y `DJANGO_SECRET_KEY`.
2. Inicia PostgreSQL:

   ```sh
   docker compose up -d db
   ```

3. Prepara y migra el backend:

   ```sh
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   `createsuperuser` crea el primer usuario con rol `admin`. El modelo de usuario personalizado debe estar configurado antes de la migración inicial; cambiar `AUTH_USER_MODEL` después de crear las tablas requiere una migración de datos planificada.

4. En otra terminal, inicia Vue:

   ```sh
   cd frontend
   npm install
   npm run dev
   ```

Vue queda disponible en `http://localhost:5173` y la comprobación de conexión con PostgreSQL en `http://localhost:8000/api/health/`. El frontend usa esa URL de API por defecto. Para cambiarla, define `VITE_API_URL` en un archivo de entorno de Vite dentro de `frontend/`. Si el frontend cambia de origen, actualiza `CORS_ALLOWED_ORIGINS` en `.env`.

## Usuarios base de prueba

Para desarrollo local, se pueden crear tres cuentas —una por rol de aplicación— mediante un comando manual. No se crean automáticamente al iniciar Django ni mediante una ruta web.

1. En el `.env` local, establece temporalmente `ALLOW_TEST_USERS=True` y configura `TEST_ADMIN_PASSWORD`, `TEST_OPERADOR_PASSWORD` y `TEST_CLIENTE_PASSWORD` con valores distintos de al menos 16 caracteres. Los correos de prueba usan el dominio reservado `.test`.
2. Ejecuta desde `backend/` después de aplicar las migraciones:

   ```sh
   python manage.py crear_usuarios_prueba --enable-test-users
   ```

El comando exige `DEBUG=True`, `ALLOW_TEST_USERS=True`, la confirmación explícita y las seis variables `TEST_*`. Es idempotente: no restablece contraseñas ni altera cuentas existentes; si el correo existe con otro rol, aborta. Las contraseñas se guardan usando el hash de Django y nunca se imprimen. Estas cuentas tienen los roles de la aplicación, pero no reciben `is_staff` ni `is_superuser`.

No uses estas cuentas ni este `.env` en producción. Al terminar las pruebas, devuelve `ALLOW_TEST_USERS=False` y elimina las tres cuentas de la base local junto con sus datos asociados. Para cualquier despliegue usa una base separada, `DJANGO_DEBUG=False`, deja `ALLOW_TEST_USERS=False` y no incluyas credenciales `TEST_*`. La opción permanece desactivada por defecto y el comando se niega a ejecutarse si falta cualquiera de las dos banderas de desarrollo.
