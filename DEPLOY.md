# Deploy Guide — Carnetruck

## Opción 1: Docker (Recomendado)

```bash
git clone https://github.com/Fernandezalejo1/carnetruck.git
cd carnetruck
cp .env.example .env

# Editar .env (opcional: cambiar JWT_SECRET)
# JWT_SECRET=tu-secreto-seguro-aqui

docker compose up -d --build

# API: http://localhost:8000/docs
# Frontend: http://localhost:8080
# Demo: admin@carnetruck.com / admin123
```

## Opción 2: Railway

1. Ir a [railway.app](https://railway.app)
2. Nuevo proyecto → "Deploy from GitHub repo"
3. Seleccionar `Fernandezalejo1/carnetruck`
4. Variables de entorno:
   - `DATABASE_URL` → PostgreSQL de Railway
   - `JWT_SECRET` → Secreto seguro
   - `SEED_DEMO` → true (para datos de demostración)
5. Deploy

## Opción 3: Render

1. Nuevo Web Service en [render.com](https://render.com)
2. Build: `cd backend && pip install -r requirements.txt`
3. Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars: `DATABASE_URL`, `JWT_SECRET`

## Credenciales Demo

| Rol | Email | Password |
|-----|-------|----------|
| Superadmin | admin@carnetruck.com | admin123 |
| Operador | operador@carnetruck.com | operador123 |

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL URL | sqlite:///./carnetruck.db |
| `JWT_SECRET` | Secreto JWT | cambia-este-secreto |
| `SEED_DEMO` | Datos demo | false |
| `ALERT_EVAL_MODE` | sync o celery | sync |

## Verificar

```bash
# Health
curl https://tu-app.railway.app/health

# Swagger
curl https://tu-app.railway.app/docs
```
