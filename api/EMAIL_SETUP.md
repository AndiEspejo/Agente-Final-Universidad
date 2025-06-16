# Configuración de Email para Reportes

Para habilitar el envío de reportes por email, necesitas configurar las siguientes variables de entorno:

## Variables de Entorno Requeridas

```bash
# Gmail Configuration
GMAIL_EMAIL=tu-email@gmail.com
GMAIL_APP_PASSWORD=tu-contraseña-de-aplicacion
```

## Configuración de Gmail

1. **Habilitar autenticación de 2 factores** en tu cuenta de Gmail
2. **Generar una contraseña de aplicación**:
   - Ve a tu cuenta de Google → Seguridad
   - En "Acceso a Google", selecciona "Contraseñas de aplicaciones"
   - Genera una nueva contraseña para "Correo"
   - Usa esta contraseña en `GMAIL_APP_PASSWORD`

## Uso del Endpoint

### POST `/analytics/send-report-email/`

```json
{
  "recipient_email": "destinatario@example.com",
  "report_type": "Análisis de Ventas",
  "charts": [
    {
      "name": "ventas_por_mes.png",
      "data": "base64_string_here"
    },
    {
      "name": "productos_mas_vendidos.png",
      "data": "base64_string_here"
    }
  ],
  "summary": "Resumen opcional del análisis"
}
```

### Respuesta

```json
{
  "success": true,
  "message": "Reporte enviado exitosamente a destinatario@example.com"
}
```

## Formato de las Imágenes

- Las imágenes deben estar en formato **base64**
- Se acepta el formato completo: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...`
- O solo la parte base64: `iVBORw0KGgoAAAANSUhEUgAA...`
- Formatos soportados: PNG, JPG, GIF

## Ejemplo de Integración Frontend

```javascript
// Obtener imagen del canvas como base64
const canvas = document.getElementById('chart-canvas');
const imageData = canvas.toDataURL('image/png');

// Enviar al backend
const response = await fetch('/analytics/send-report-email/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    recipient_email: 'usuario@example.com',
    report_type: 'Análisis de Inventario',
    charts: [
      {
        name: 'inventario_actual.png',
        data: imageData,
      },
    ],
    summary: 'Análisis del estado actual del inventario',
  }),
});
```
