<script setup>
import { onMounted, ref } from 'vue'

const apiStatus = ref('Comprobando API...')
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const usuario = ref(null)
const tokenInvitacion = ref(new URLSearchParams(window.location.search).get('token') || '')
const email = ref('')
const password = ref('')
const emailInvitacion = ref('')
const nombreInvitacion = ref('')
const apellidosInvitacion = ref('')
const rolInvitacion = ref('operador')
const mensaje = ref('')
const error = ref('')
const ocupado = ref(false)
const invitacionAceptada = ref(false)

function cookie(name) {
  const prefix = `${name}=`
  const item = document.cookie.split('; ').find((part) => part.startsWith(prefix))
  return item ? decodeURIComponent(item.slice(prefix.length)) : ''
}

async function request(path, options = {}) {
  const method = options.method || 'GET'
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    await fetch(`${apiBaseUrl}/auth/csrf/`, { credentials: 'include' })
  }
  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(cookie('csrftoken') ? { 'X-CSRFToken': cookie('csrftoken') } : {}),
      ...options.headers,
    },
  })
  const data = response.status === 204 ? null : await response.json()
  if (!response.ok) {
    const requestError = new Error(
      data?.detail || Object.values(data || {}).flat().join(' ') || 'Ocurrió un error.',
    )
    requestError.status = response.status
    throw requestError
  }
  return data
}

onMounted(async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/health/`)
    if (!response.ok) throw new Error('API unavailable')
    const data = await response.json()
    apiStatus.value = `API conectada · PostgreSQL ${data.database}`
  } catch {
    apiStatus.value = 'API sin conexion'
  }

  try {
    await fetch(`${apiBaseUrl}/auth/csrf/`, { credentials: 'include' })
    if (!tokenInvitacion.value) {
      usuario.value = await request('/auth/me/')
    }
  } catch (requestError) {
    if (!tokenInvitacion.value && ![401, 403].includes(requestError.status)) {
      error.value = 'No se pudo conectar con el servicio de autenticación.'
    }
  }
})

async function iniciarSesion() {
  ocupado.value = true
  error.value = ''
  try {
    usuario.value = await request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    password.value = ''
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    ocupado.value = false
  }
}

async function aceptarInvitacion() {
  ocupado.value = true
  error.value = ''
  try {
    const result = await request('/auth/invitations/accept/', {
      method: 'POST',
      body: JSON.stringify({ token: tokenInvitacion.value, password: password.value }),
    })
    email.value = result.email
    password.value = ''
    tokenInvitacion.value = ''
    invitacionAceptada.value = true
    window.history.replaceState({}, '', window.location.pathname)
    mensaje.value = result.detail
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    ocupado.value = false
  }
}

async function cerrarSesion() {
  ocupado.value = true
  error.value = ''
  try {
    await request('/auth/logout/', { method: 'POST' })
    usuario.value = null
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    ocupado.value = false
  }
}

async function enviarInvitacion() {
  ocupado.value = true
  error.value = ''
  mensaje.value = ''
  try {
    const result = await request('/auth/invitations/', {
      method: 'POST',
      body: JSON.stringify({
        email: emailInvitacion.value,
        nombre: nombreInvitacion.value,
        apellidos: apellidosInvitacion.value,
        rol: rolInvitacion.value,
      }),
    })
    mensaje.value = `Invitación enviada a ${result.email}.`
    emailInvitacion.value = ''
    nombreInvitacion.value = ''
    apellidosInvitacion.value = ''
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    ocupado.value = false
  }
}
</script>

<template>
  <main class="shell">
    <p class="eyebrow">Proyecto inicializado</p>
    <section class="auth-card">
      <h1>KCR</h1>
      <p class="stack">Catálogos y usuarios</p>

      <div v-if="usuario" class="account">
        <p>Sesión iniciada como <strong>{{ usuario.nombre }} {{ usuario.apellidos }}</strong></p>
        <p>{{ usuario.email }} · {{ usuario.rol }}</p>
        <form v-if="usuario.rol === 'admin'" class="form invite-form" @submit.prevent="enviarInvitacion">
          <h2>Invitar usuario</h2>
          <label for="invite-email">Correo electrónico</label>
          <input id="invite-email" v-model="emailInvitacion" type="email" required>
          <label for="invite-name">Nombre</label>
          <input id="invite-name" v-model="nombreInvitacion" required>
          <label for="invite-surname">Apellidos</label>
          <input id="invite-surname" v-model="apellidosInvitacion" required>
          <label for="invite-role">Rol</label>
          <select id="invite-role" v-model="rolInvitacion">
            <option value="operador">Operador</option>
            <option value="cliente">Cliente</option>
          </select>
          <button type="submit" :disabled="ocupado">Enviar invitación</button>
        </form>
        <button type="button" :disabled="ocupado" @click="cerrarSesion">Cerrar sesión</button>
      </div>

      <form v-else-if="tokenInvitacion" class="form" @submit.prevent="aceptarInvitacion">
        <h2>Activa tu cuenta</h2>
        <p>Define una contraseña para completar la invitación.</p>
        <label for="invite-password">Contraseña (mínimo 12 caracteres)</label>
        <input
          id="invite-password"
          v-model="password"
          type="password"
          minlength="12"
          autocomplete="new-password"
          required
        >
        <button type="submit" :disabled="ocupado">Definir contraseña</button>
      </form>

      <form v-else class="form" @submit.prevent="iniciarSesion">
        <h2>{{ invitacionAceptada ? 'Ya puedes iniciar sesión' : 'Iniciar sesión' }}</h2>
        <label for="email">Correo electrónico</label>
        <input id="email" v-model="email" type="email" autocomplete="username" required>
        <label for="password">Contraseña</label>
        <input id="password" v-model="password" type="password" autocomplete="current-password" required>
        <button type="submit" :disabled="ocupado">Entrar</button>
      </form>

      <p v-if="mensaje" class="notice" role="status">{{ mensaje }}</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </section>
    <p class="status" role="status">{{ apiStatus }}</p>
  </main>
</template>
