export const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function leerRespuesta(response) {
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

    if (datos && typeof datos === 'object') {
      const errorValidacion = Object.values(datos)
        .flatMap((errores) => Array.isArray(errores) ? errores : [errores])
        .find((error) => typeof error === 'string')
      if (errorValidacion) {
        throw new Error(errorValidacion)
      }
    }

    throw new Error('No se pudo completar la solicitud. Revisa tus datos e inténtalo de nuevo.')
  }

  return datos
}

export function tokenCSRF() {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith('csrftoken='))

  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''
}
