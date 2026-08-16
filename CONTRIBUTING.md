# Contributing a Carnetruck

Gracias por querer contribuir! Este documento explica cómo configurar el entorno de desarrollo.

## 🚀 Requisitos previos

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (recomendado)
- PostgreSQL (o SQLite para desarrollo local)

## 🔧 Setup de desarrollo

### Opción A: Docker (recomendada)

```bash
git clone https://github.com/Fernandezalejo1/carnetruck.git
cd carnetruck
cp .env.example .env
docker compose up -d --build
```

### Opción B: Desarrollo local

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./carnetruck.db SEED_DEMO=true \
  uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest -v

# Con cobertura
pytest --cov=app --cov-report=html
```

### Convenciones de tests

- Archivos: `test_*.py` en `backend/tests/`
- Usar `conftest.py` para fixtures compartidos
- Tests de aislamiento multi-tenant
- Tests de integridad de hash

## 🎨 Código y estilo

- **Python**: Seguir PEP 8, usar type hints
- **JavaScript**: ESLint + Prettier
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)

### Formato de commits

```
feat: agregar endpoint de MQTT
fix: corregir cálculo de alertas
docs: actualizar README
test: agregar tests de integridad
refactor: extraer lógica de alertas
```

## 🏗️ Estructura del proyecto

```
carnetruck/
├── backend/
│   ├── app/
│   │   ├── api/         # Endpoints (auth, ingest, shipments, devices, certificates)
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── workers/     # Celery tasks
│   └── tests/           # pytest
├── frontend/            # React + Vite + Tailwind
└── docker-compose.yml
```

## 🔒 Seguridad

- Nunca commitear `.env` o secrets
- Usar variables de entorno para configuración sensible
- Reportar vulnerabilidades a [SECURITY.md](SECURITY.md)

## 📝 Pull Requests

1. Crear branch desde `main`: `git checkout -b feat/nombre-feature`
2. Hacer cambios con commits descriptivos
3. Ejecutar `pytest` y verificar que pasa
4. Abrir PR con descripción clara
5. Esperar revisión y CI verde
