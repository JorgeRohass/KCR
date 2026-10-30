<script setup>
import { onMounted, ref } from 'vue'
import AccountPage from './components/AccountPage.vue'
import InvitationPage from './components/InvitationPage.vue'
import LoginPage from './components/LoginPage.vue'
import { apiUrl, leerRespuesta } from './services/api.js'

const usuario = ref(null)
const cargando = ref(true)
const vista = ref('login')
const tokenInvitacion = ref('')
const mensaje = ref('')

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

function cerrarSesion() {
  usuario.value = null
  vista.value = 'login'
  mensaje.value = ''
}

onMounted(async () => {
  const url = new URL(window.location.href)
  if (url.searchParams.has('invitation_token')) {
    tokenInvitacion.value = url.searchParams.get('invitation_token') || ''
    vista.value = 'invitation'
    url.searchParams.delete('invitation_token')
    window.history.replaceState(
      {},
      '',
      `${url.pathname}${url.search}${url.hash}`,
    )
    cargando.value = false
    return
  }

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

      <InvitationPage
        v-else-if="vista === 'invitation'"
        :token="tokenInvitacion"
        @return-to-login="vista = 'login'"
      />

      <AccountPage
        v-else-if="usuario"
        :usuario="usuario"
        @logged-out="cerrarSesion"
      />

      <LoginPage
        v-else
        :mensaje="mensaje"
        @authenticated="usuario = $event"
      />
    </div>
  </main>
</template>
