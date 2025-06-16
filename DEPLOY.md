# 🚀 Guía de Deploy - LangGraph Sales/Inventory System

## Opciones de Deploy

### 1. 🐳 Deploy con Docker (Recomendado)

#### Opción A: Docker Compose (Más Fácil)

```bash
# Construir y ejecutar ambos servicios
docker-compose up --build

# En modo detached (background)
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Parar servicios
docker-compose down
```

#### Opción B: Docker Individual

```bash
# Construir API
cd api
docker build -t sales-api .

# Construir Frontend
cd frontend
docker build -t sales-frontend .

# Ejecutar API
docker run -p 8000:8000 sales-api

# Ejecutar Frontend
docker run -p 3000:3000 sales-frontend
```

### 2. ☁️ Deploy en Vercel (Frontend) + Railway (API)

#### Frontend en Vercel:

```bash
cd frontend
npm install -g vercel
vercel --prod
```

#### API en Railway:

1. Crear cuenta en railway.app
2. Conectar repositorio
3. Configurar variables de entorno
4. Deploy automático

### 3. 🌐 Deploy en Render

#### API en Render:

1. Crear Web Service en render.com
2. Conectar repositorio
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11

#### Frontend en Render:

1. Crear Static Site
2. Build Command: `npm run build`
3. Publish Directory: `.next`

### 4. 🚀 Deploy Manual

#### API (FastAPI):

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend (Next.js):

```bash
cd frontend
npm install
npm run build
npm start
```

## Variables de Entorno

### API (.env):

```env
# AI/LangGraph
GOOGLE_API_KEY=tu_google_api_key_aqui

# Database
DATABASE_URL=sqlite:///./sales_inventory.db

# JWT
JWT_SECRET_KEY=tu_jwt_secret_muy_seguro
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@gmail.com
SMTP_PASSWORD=tu_password_app
```

### Frontend (.env.local):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Configuración para Producción

### 1. Seguridad

- Cambiar `JWT_SECRET_KEY` por uno seguro
- Configurar CORS para dominios específicos
- Usar HTTPS en producción

### 2. Base de Datos

- Para producción, considera PostgreSQL:

```bash
pip install asyncpg
# Cambiar DATABASE_URL a postgres://...
```

### 3. Variables de Entorno Producción

```env
# API
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:port/db
API_HOST=https://tu-api.railway.app

# Frontend
NEXT_PUBLIC_API_URL=https://tu-api.railway.app
```

## Verificación del Deploy

### Endpoints a Probar:

- API: `GET /` - Información del API
- API: `GET /auth/me` - Autenticación
- Frontend: `http://localhost:3000` - Página principal

### Comandos de Verificación:

```bash
# Verificar API
curl http://localhost:8000/

# Verificar Frontend
curl http://localhost:3000/
```

## Solución de Problemas

### Problemas Comunes:

1. **Error de CORS**: Configurar origins en `main.py`
2. **Base de datos**: Verificar que `sales_inventory.db` tenga permisos
3. **Dependencias**: Instalar todas las dependencias de `requirements.txt`
4. **Puerto ocupado**: Cambiar puertos en configuración

### Logs Útiles:

```bash
# Docker logs
docker-compose logs api
docker-compose logs frontend

# Python logs
python -m uvicorn main:app --reload --log-level debug

# Next.js logs
npm run dev
```

## Recursos Adicionales

- [FastAPI Deploy Guide](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deploy Guide](https://nextjs.org/docs/deployment)
- [Docker Compose Guide](https://docs.docker.com/compose/)
