<script setup>
import { onMounted, ref } from 'vue'

const apiStatus = ref('Comprobando API...')
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

onMounted(async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/health/`)
    if (!response.ok) throw new Error('API no disponible')
    const data = await response.json()
    apiStatus.value = data.database === 'connected'
      ? 'API conectada · PostgreSQL disponible'
      : 'API disponible, pero PostgreSQL no está conectado'
  } catch {
    apiStatus.value = 'API sin conexión'
  }
})
</script>

<template>
  <main class="shell">
    <p class="eyebrow">Esquema de datos configurado</p>
    <h1>KCR</h1>
    <p class="stack">Vue <span>+</span> Django <span>+</span> PostgreSQL</p>
    <p class="status" role="status">{{ apiStatus }}</p>

    <section aria-labelledby="schema-title">
      <h2 id="schema-title">Modelo de la aplicación</h2>
      <p>Los tres perfiles comparten una cuenta de usuario; el rol indica si es administrador, operador o cliente.</p>
      <ul>
        <li><strong>Usuario:</strong> identidad, correo, contraseña y rol.</li>
        <li><strong>Invitación:</strong> usuario invitado, creador, hash del token, vencimiento y uso.</li>
        <li><strong>Catálogo:</strong> pertenece a un cliente y puede tener varios operadores.</li>
        <li><strong>Productos e historial:</strong> vinculados al catálogo; cada cambio registra su editor.</li>
      </ul>
      <p>La API actual comprueba la conexión con PostgreSQL. El inicio de sesión y el envío o aceptación de invitaciones todavía no están implementados.</p>
    </section>
  </main>
</template>
