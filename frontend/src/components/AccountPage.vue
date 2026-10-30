<script setup>
import { ref } from 'vue'
import { apiUrl, leerRespuesta, tokenCSRF } from '../services/api.js'

defineProps({
  usuario: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['logged-out'])
const procesando = ref(false)
const mensaje = ref('')

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
    emit('logged-out')
  } catch (error) {
    mensaje.value = error instanceof Error
      ? error.message
      : 'No se pudo cerrar la sesión.'
  } finally {
    procesando.value = false
  }
}
</script>

<template>
  <section class="login-card account-card" aria-labelledby="account-title">
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
</template>
