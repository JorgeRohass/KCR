<script setup>
import { onMounted, ref } from 'vue'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const email = ref('')
const password = ref('')
const mostrarPassword = ref(false)
const mensaje = ref('')
const usuario = ref(null)
const cargando = ref(true)
const procesando = ref(false)

function tokenCSRF() {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith('csrftoken='))

  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''
}

async function leerRespuesta(response) {
  let datos
  try {
    datos = await response.json()
  } catch {
    throw new Error('El servidor devolvió una respuesta inválida.')
  }

  if (!response.ok) {
    if (typeof datos.detail === 'string') {
      throw new Error(datos.detail)
    }

    throw new Error('No se pudo completar la solicitud. Revisa tus datos e inténtalo de nuevo.')
  }

  return datos
}

async function cargarUsuario() {
  const response = await fetch(`${apiUrl}/api/auth/me/`, {
    credentials: 'include',
  })

  if (response.status === 403 || response.status === 401) {
    usuario.value = null
    return false
  }

  usuario.value = await leerRespuesta(response)
  return true
}

async function iniciarSesion() {
  mensaje.value = ''
  procesando.value = true

  try {
    const response = await fetch(`${apiUrl}/api/auth/login/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    await leerRespuesta(response)
    if (!(await cargarUsuario())) {
      throw new Error('No se pudo recuperar la sesión después de iniciar sesión.')
    }

    password.value = ''
  } catch (error) {
    mensaje.value = error instanceof Error
      ? error.message
      : 'No se pudo conectar con el servidor.'
  } finally {
    procesando.value = false
  }
}

async function cerrarSesion() {
  mensaje.value = ''
  procesando.value = true

  try {
    const response = await fetch(`${apiUrl}/api/auth/logout/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': tokenCSRF() },
    })

    await leerRespuesta(response)
    usuario.value = null
    email.value = ''
    password.value = ''
  } catch (error) {
    mensaje.value = error instanceof Error
      ? error.message
      : 'No se pudo cerrar la sesión.'
  } finally {
    procesando.value = false
  }
}

function recuperarPassword() {
  mensaje.value = 'La recuperación de contraseña todavía no está disponible.'
}

onMounted(async () => {
  try {
    await cargarUsuario()
  } catch (error) {
    mensaje.value = error instanceof Error
      ? error.message
      : 'No se pudo conectar con el servidor.'
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <main class="login-page">
    <div class="login-content">
      <div class="brand-mark" role="img" aria-label="Empresa"></div>

      <section v-if="cargando" class="login-card" aria-live="polite">
        <p class="form-message">Comprobando sesión...</p>
      </section>

      <section v-else-if="usuario" class="login-card account-card" aria-labelledby="account-title">
        <header class="login-header">
          <h1 id="account-title">Hola, {{ usuario.nombre_completo }}</h1>
          <p>Tu cuenta está activa.</p>
        </header>
        <p class="role-label">Rol</p>
        <p class="role-value">{{ usuario.rol_nombre }}</p>
        <button
          class="submit-button"
          type="button"
          :disabled="procesando"
          @click="cerrarSesion"
        >
          {{ procesando ? 'Cerrando sesión...' : 'Cerrar sesión' }}
        </button>
        <p v-if="mensaje" class="form-message" role="alert">{{ mensaje }}</p>
      </section>

      <section v-else class="login-card" aria-labelledby="login-title">
        <header class="login-header">
          <h1 id="login-title">Iniciar sesión</h1>
          <p>Introduce tus datos para acceder a tu cuenta Empresa.</p>
        </header>

        <form class="login-form" @submit.prevent="iniciarSesion">
          <div class="field">
            <label for="email">Correo electrónico</label>
            <input
              id="email"
              v-model="email"
              type="email"
              name="email"
              placeholder="tu@ejemplo.com"
              autocomplete="username"
              required
            >
          </div>

          <div class="field">
            <label for="password">Contraseña</label>
            <div class="password-input">
              <input
                id="password"
                v-model="password"
                :type="mostrarPassword ? 'text' : 'password'"
                name="password"
                placeholder="Introduce tu contraseña"
                autocomplete="current-password"
                required
              >
              <button
                class="visibility-toggle"
                type="button"
                :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                :aria-pressed="mostrarPassword"
                @click="mostrarPassword = !mostrarPassword"
              >
                <svg
                  v-if="mostrarPassword"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <path d="M3 3l18 18M10.6 10.7a2 2 0 002.7 2.7" />
                  <path d="M9.9 5.2A10.8 10.8 0 0112 5c5 0 8.5 4.5 9.5 6-.4.7-1.4 2-2.9 3.3M6.2 6.3C4.2 7.5 2.9 9.4 2.5 11c1 1.5 4.5 6 9.5 6 1 0 2-.2 2.8-.5" />
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>
            </div>
          </div>

          <div class="forgot-password">
            <button type="button" @click="recuperarPassword">¿Olvidaste tu contraseña?</button>
          </div>

          <button class="submit-button" type="submit" :disabled="procesando">
            {{ procesando ? 'Ingresando...' : 'Iniciar sesión' }}
          </button>
          <p v-if="mensaje" class="form-message" role="alert">{{ mensaje }}</p>
        </form>
      </section>
    </div>
  </main>
</template>
