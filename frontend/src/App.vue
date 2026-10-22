<script setup>
import { onMounted, ref } from 'vue'

const apiStatus = ref('Comprobando API...')
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

onMounted(async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/health/`)
    if (!response.ok) throw new Error('API unavailable')
    const data = await response.json()
    apiStatus.value = `API conectada · PostgreSQL ${data.database}`
  } catch {
    apiStatus.value = 'API sin conexion'
  }
})
</script>

<template>
  <main class="shell">
    <p class="eyebrow">Proyecto inicializado</p>
    <h1>KCR</h1>
    <p class="stack">Vue <span>+</span> Django <span>+</span> PostgreSQL</p>
    <p class="status" role="status">{{ apiStatus }}</p>
  </main>
</template>
