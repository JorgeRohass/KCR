<script setup>
import { ref } from 'vue'

const email = ref('')
const password = ref('')
const mostrarPassword = ref(false)
const mensaje = ref('')

function iniciarSesion() {
  mensaje.value = 'El inicio de sesión estará disponible cuando se implemente la API de autenticación.'
}

function recuperarPassword() {
  mensaje.value = 'La recuperación de contraseña todavía no está disponible.'
}
</script>

<template>
  <main class="login-page">
    <div class="login-content">
      <div class="brand-mark" role="img" aria-label="Empresa"></div>

      <section class="login-card" aria-labelledby="login-title">
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

          <button class="submit-button" type="submit">Iniciar sesión</button>
          <p v-if="mensaje" class="form-message" role="status">{{ mensaje }}</p>
        </form>
      </section>
    </div>
  </main>
</template>
