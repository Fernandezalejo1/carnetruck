# Changelog

Todos los cambios notables en Carnetruck serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y el proyecto adherido a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Rate limiting middleware (200 req/min por IP)
- Request tracking middleware (X-Request-Id, X-Response-Time)
- Tests de autenticación (login, tokens, roles)
- Tests de integridad de hash (edge cases, tamper detection)
- Tests de generación de certificados
- GitHub Actions CI/CD (backend tests, frontend build, Docker build)
- CONTRIBUTING.md con guías de desarrollo
- SECURITY.md con política de reporte de vulnerabilidades
- CHANGELOG.md
- README mejorado con badges y documentación completa

### Changed
- CORS restringido a métodos y headers específicos
- main.py refactorizado con middleware de seguridad

### Security
- Rate limiting para prevenir abuso de API
- CORS restringido (no más allow all)
- Request tracking para auditoría

## [0.1.0] - 2026-08-17

### Added
- Backend FastAPI con autenticación JWT
- Multi-tenant aislamiento completo
- Ingesta dual de sensores (NBM1 + BLE)
- Integridad inmutable SHA-256 encadenado
- Motor de reglas de alertas con cooldown
- Generación de certificados PDF (WeasyPrint + fallback)
- Dashboard React con mapa en vivo (Leaflet)
- Docker Compose completo (TimescaleDB, Redis, Celery, MQTT)
- 20 tests iniciales
- Licencia MIT
