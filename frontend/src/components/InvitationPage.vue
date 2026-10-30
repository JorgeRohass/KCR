<script setup>
import { ref } from 'vue'
import { apiUrl, leerRespuesta } from '../services/api.js'

defineProps({
  token: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['return-to-login'])
const nuevaPassword = ref('')
const confirmarPassword = ref('')
const procesando = ref(false)
const mensaje = ref('')
const invitacionAceptada = ref(false)

async function aceptarInvitacion(token) {
  mensaje.value = ''
  procesando.value = true

  try {
    const response = await fetch(`${apiUrl}/api/auth/invitations/accept/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        password: nuevaPassword.value,
        confirmar_password: confirmarPassword.value,
      }),
    })

    await leerRespuesta(response)
    invitacionAceptada.value = true
    nuevaPassword.value = ''
    confirmarPassword.value = ''
  } catch (error) {
    mensaje.value = error instanceof Error
      ? error.message
      : 'No se pudo activar la cuenta.'
  } finally {
    procesando.value = false
  }
}
</script>

<template>
  <section class="login-card" aria-labelledby="invitation-title">
    <template v-if="invitacionAceptada">
      <header class="login-header">
        <h1 id="invitation-title">Cuenta activada</h1>
        <p>Ya puedes iniciar sesión con tu nueva contraseña.</p>
      </header>
      <button
        class="submit-button"
        type="button"
        @click="emit('return-to-login')"
      >
        Ir a iniciar sesión
      </button>
    </template>

    <template v-else>
      <header class="login-header">
        <h1 id="invitation-title">Activa tu cuenta</h1>
        <p>Define una contraseña para completar tu invitación.</p>
      </header>

      <form class="login-form" @submit.prevent="aceptarInvitacion(token)">
        <div class="field">
          <label for="new-password">Contraseña</label>
          <input
            id="new-password"
            v-model="nuevaPassword"
            type="password"
            name="new-password"
            autocomplete="new-password"
            minlength="8"
            required
          >
        </div>
        <div class="field">
          <label for="confirm-password">Confirma la contraseña</label>
          <input
            id="confirm-password"
            v-model="confirmarPassword"
            type="password"
            name="confirm-password"
            autocomplete="new-password"
            minlength="8"
            required
          >
        </div>
        <button class="submit-button" type="submit" :disabled="procesando">
          {{ procesando ? 'Activando cuenta...' : 'Activar cuenta' }}
        </button>
        <p v-if="mensaje" class="form-message" role="alert">{{ mensaje }}</p>
      </form>
    </template>
  </section>
</template>
