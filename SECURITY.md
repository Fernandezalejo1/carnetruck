# Política de Seguridad

## Reportar Vulnerabilidades

Si descubres una vulnerabilidad de seguridad, por favor **no** la reportes en un issue público. En su lugar:

1. Envía un email a **[tu-email@ejemplo.com]** con:
   - Descripción de la vulnerabilidad
   - Pasos para reproducir
   - Impacto potencial
   - Sugiere una corrección (opcional)

2. Respuesta esperada:
   - Confirmación de recepción en 48 horas
   - Evaluación en 5 días hábiles
   - Corrección o mitigación según prioridad

## Medidas de seguridad implementadas

### Autenticación
- JWT tokens con expiración configurable
- Password hashing con PBKDF2 (120,000 iteraciones + salt único)
- Device keys únicas por sensor

### Autorización
- Multi-tenant: aislamiento completo por frigorífico/exportador
- Roles: superadmin, admin, operador, viewer
- Validación de tenant en cada request

### Integridad de datos
- SHA-256 encadenado por lectura (tamper-evident)
- Hash del documento cubre cadena completa + metadatos
- Endpoint de verificación que recomputa integridad

### Rate Limiting
- 200 requests por minuto por IP
- Protección contra abuso de API

### CORS
- Orígenes configurados via `CORS_ORIGINS`
- Métodos y headers explícitos

### Request Tracking
- X-Request-Id en cada respuesta
- X-Response-Time para monitoreo
- Logging estructurado

### Infraestructura
- Secrets en variables de entorno (nunca en código)
- `.gitignore` excluye `.env`, bases de datos
- Docker multi-stage builds
- Celery workers aislados

## Dependencias

Usamos Dependabot para mantener las dependencias actualizadas y alertar sobre vulnerabilidades conocidas.

## Actualizaciones de seguridad

Las actualizaciones de seguridad se publicarán como patch versions (ej: `0.1.1`).
