# EMPRESA

Base full-stack con Vue 3, Django REST Framework y PostgreSQL.

## Requisitos

- Python 3.12+
- Node.js 20+
- Docker Compose

## Esquema de datos

El diagrama de las tablas propias de la aplicación y sus relaciones está en [docs/Esquema.png](docs/Esquema.png).

La app Django `catalogo` define estas tablas:

- `usuario`: identidad común con correo, teléfono (`fono`), contraseña almacenada con el hash de Django y rol (`admin`, `operador` o `cliente`).
- `invitacion`: usuario invitado, usuario creador, hash del token, vencimiento y fecha de uso.
- `catalogo`: pertenece a un cliente y registra el usuario que lo creó.
- `catalogo_operador`: relación muchos-a-muchos entre catálogos y operadores.
- `producto`: productos pertenecientes a un catálogo.
- `version_catalogo`: versión numerada del catálogo, con editor, fecha y motivo.
- `producto_version`: copia completa de los productos que pertenecen a cada versión.

Los tres roles son valores de `usuario.rol`, no tablas separadas. Un administrador autenticado puede crear invitaciones para operadores y clientes mediante `POST /api/invitations/`; solo el administrador principal puede invitar a otros administradores. La respuesta incluye el enlace para compartirlo manualmente, sin envío automático. El enlace usa el parámetro `invitation_token`, abre el formulario del frontend y `POST /api/auth/invitations/accept/` valida el token y activa la cuenta al guardar la contraseña. La recuperación de contraseña podrá usar un parámetro y un endpoint separados para que no se confundan ambos propósitos. Los tokens son aleatorios, se almacena solo su hash y expiran en siete días por defecto; `INVITATION_TTL_DAYS` permite cambiar ese plazo. `FRONTEND_BASE_URL` define el origen usado al construir el enlace. El token solo se devuelve al crear la invitación, así que debe compartirse por un canal seguro.

El endpoint de creación recibe `email`, `nombre`, `apellidos` y `rol` (`operador`, `cliente` o `admin` según los permisos del creador). El endpoint de aceptación recibe `token`, `password` y `confirmar_password`. El modelo de usuario actual requiere correo electrónico como identificador de inicio de sesión; el canal por el que se comparte el enlace queda desacoplado de ese correo, por lo que puede conectarse posteriormente a un servicio de SMS sin cambiar la validación del token.

La API también incluye `GET /api/health/`, `POST /api/auth/login/`, `POST /api/auth/logout/` y `GET /api/auth/me/`.

El inicio de sesión recibe JSON con `email` y `password`. Si las credenciales son válidas y la cuenta está activa, establece una sesión Django mediante cookie, sin restringir por rol (`admin`, `operador` o `cliente`). Responde `200` al iniciar sesión, `401` si las credenciales no son válidas o la cuenta está inactiva y `400` si los datos son inválidos. El cierre de sesión requiere una sesión autenticada, la invalida y responde `200`; sin autenticación responde `403`. `GET /api/auth/me/` devuelve nombre completo y rol de la sesión actual, y responde `403` si no hay sesión. El frontend conserva la sesión mediante cookies y muestra esos datos al ingresar o recargar la página.

El backend permite crear una foto completa del catálogo con `guardar_version_catalogo(catalogo, editor, motivo)` y restaurar una versión con `restaurar_version_catalogo(version, editor, motivo)`, desde `catalogo.services`. Ambas operaciones son transaccionales. Una restauración reemplaza los productos actuales y registra el resultado como una versión nueva, enlazada con `restaurada_desde`; no elimina el historial previo.

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
   python manage.py runserver
   ```

   La base de datos debe estar migrada y el modelo de usuario personalizado configurado antes de la migración inicial.

   `createsuperuser` es una operación separada, reservada para una cuenta técnica que necesite administrar Django. No la uses para crear administradores normales de la aplicación.

4. En otra terminal, inicia Vue:

   ```sh
   cd frontend
   npm install
   npm run dev
   ```

Vue queda disponible en `http://localhost:5173` y la comprobación de conexión con PostgreSQL en `http://localhost:8000/api/health/`. El frontend usa esa URL de API por defecto. Para cambiarla, define `VITE_API_URL` en un archivo de entorno de Vite dentro de `frontend/`. Si el frontend cambia de origen, actualiza `CORS_ALLOWED_ORIGINS` en `.env`.

## Crear el administrador principal

Después de aplicar las migraciones y antes de crear otras cuentas, ejecuta el comando desde `backend/`:

```sh
python manage.py crear_admin_principal \
  --email admin@tu-dominio.com \
  --nombre Admin \
  --apellidos Principal \
  --confirmar
```

El comando solo funciona si la tabla de usuarios está vacía. Solicita la contraseña dos veces en la terminal, requiere al menos 16 caracteres y crea el primer usuario con rol `admin` y `puede_crear_administradores=True`. No imprime ni recibe la contraseña como argumento y no concede `is_staff` ni `is_superuser`; por tanto, esa cuenta no obtiene acceso al admin interno de Django.

## Usuarios base de prueba

Para desarrollo local, se pueden crear tres cuentas —una por rol de aplicación— mediante un comando manual. No se crean automáticamente al iniciar Django ni mediante una ruta web.

1. En el `.env` local, establece temporalmente `ALLOW_TEST_USERS=True` y configura `TEST_ADMIN_PASSWORD`, `TEST_OPERADOR_PASSWORD` y `TEST_CLIENTE_PASSWORD` con valores distintos de al menos 16 caracteres. Los correos de prueba usan el dominio reservado `.test`.
2. Ejecuta desde `backend/` después de aplicar las migraciones:

   ```sh
   python manage.py crear_usuarios_prueba --enable-test-users
   ```

El comando exige `DEBUG=True`, `ALLOW_TEST_USERS=True`, la confirmación explícita y las seis variables `TEST_*`. Es idempotente: no restablece contraseñas ni altera cuentas existentes; si el correo existe con otro rol, aborta. Las contraseñas se guardan usando el hash de Django y nunca se imprimen. Estas cuentas tienen los roles de la aplicación, pero no reciben `is_staff` ni `is_superuser`.

No uses estas cuentas ni este `.env` en producción. Al terminar las pruebas, devuelve `ALLOW_TEST_USERS=False` y elimina las tres cuentas de la base local junto con sus datos asociados. Para cualquier despliegue usa una base separada, `DJANGO_DEBUG=False`, deja `ALLOW_TEST_USERS=False` y no incluyas credenciales `TEST_*`. La opción permanece desactivada por defecto y el comando se niega a ejecutarse si falta cualquiera de las dos banderas de desarrollo.
