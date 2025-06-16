# ☁️ Deploy en la Nube - Guía Paso a Paso

## 🎯 **Opción 1: Vercel + Railway (RECOMENDADO)**

### **Paso 1: Deploy del Frontend en Vercel**

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Ir al directorio del frontend
cd frontend

# 3. Login en Vercel
vercel login

# 4. Deploy
vercel --prod
```

**Configuración en Vercel Dashboard:**

- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: `https://tu-api.railway.app` (obtienes esto después del step 2)

### **Paso 2: Deploy del API en Railway**

1. Ve a [railway.app](https://railway.app)
2. Login con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Selecciona tu repositorio
5. Configura variables de entorno:
   - `GOOGLE_API_KEY`: tu API key de Google
   - `JWT_SECRET_KEY`: genera uno seguro
   - `DATABASE_URL`: `sqlite:///./sales_inventory.db`
   - `PORT`: Railway lo configura automáticamente

### **Paso 3: Actualizar Frontend**

Vuelve a Vercel y actualiza `NEXT_PUBLIC_API_URL` con la URL de Railway.

---

## 🌐 **Opción 2: Render (Todo en Uno)**

### **Paso 1: Deploy usando render.yaml**

1. Ve a [render.com](https://render.com)
2. "New" → "Blueprint"
3. Conecta tu repositorio
4. Render detectará automáticamente el `render.yaml`
5. Configura variables de entorno:
   - `GOOGLE_API_KEY`: tu API key de Google

### **Paso 2: Verificar Deploy**

- API: `https://tu-app-api.onrender.com`
- Frontend: `https://tu-app-frontend.onrender.com`

---

## 🐳 **Opción 3: DigitalOcean App Platform**

### **Paso 1: Crear App**

```bash
# 1. Instalar doctl
brew install doctl  # macOS
# o descargar desde digitalocean.com

# 2. Login
doctl auth init

# 3. Deploy
doctl apps create-deployment
```

### **Configuración:**

- Build Command (API): `pip install -r requirements.txt`
- Run Command (API): `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Build Command (Frontend): `npm run build`
- Run Command (Frontend): `npm start`

---

## 🚀 **Opción 4: Heroku (Clásica)**

### **API en Heroku:**

```bash
# 1. Instalar Heroku CLI
# 2. Login
heroku login

# 3. Crear app
cd api
heroku create tu-sales-api

# 4. Deploy
git subtree push --prefix=api heroku main

# 5. Configurar variables
heroku config:set GOOGLE_API_KEY=tu_key
heroku config:set JWT_SECRET_KEY=tu_secret
```

### **Frontend en Heroku:**

```bash
cd frontend
heroku create tu-sales-frontend
git subtree push --prefix=frontend heroku main
heroku config:set NEXT_PUBLIC_API_URL=https://tu-sales-api.herokuapp.com
```

---

## ⚙️ **Variables de Entorno por Plataforma**

### **Para Todas las Plataformas:**

#### API:

```env
GOOGLE_API_KEY=tu_google_api_key_aqui
JWT_SECRET_KEY=tu_super_secret_key_muy_largo_y_seguro
DATABASE_URL=sqlite:///./sales_inventory.db
ENVIRONMENT=production
```

#### Frontend:

```env
NEXT_PUBLIC_API_URL=https://tu-api-url.com
NODE_ENV=production
```

### **Generador de JWT Secret:**

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

---

## 🔒 **Configuración de Seguridad**

### **1. CORS Actualizado**

Ya está configurado en `main.py` para aceptar dominios de producción.

### **2. HTTPS**

Todas las plataformas proporcionan HTTPS automáticamente.

### **3. Variables de Entorno Seguras**

- Nunca commits `.env` files
- Usa los dashboards de las plataformas para configurar secrets

---

## ✅ **Verificación del Deploy**

### **Endpoints a Probar:**

```bash
# API Health Check
curl https://tu-api-url.com/

# Frontend
curl https://tu-frontend-url.com/
```

### **Checklist Post-Deploy:**

- [ ] API responde en `/`
- [ ] Frontend carga correctamente
- [ ] Autenticación funciona
- [ ] Chat funciona
- [ ] CORS configurado correctamente
- [ ] Variables de entorno configuradas
- [ ] HTTPS habilitado

---

## 🆘 **Solución de Problemas**

### **Errores Comunes:**

1. **CORS Error:**

   - Verificar que la URL del frontend esté en `allow_origins`
   - Usar HTTPS en producción

2. **API Key Error:**

   - Verificar que `GOOGLE_API_KEY` esté configurada
   - Verificar permisos de la API key

3. **Database Error:**

   - Para producción, considera PostgreSQL
   - Verificar permisos de escritura

4. **Build Failures:**
   - Verificar versiones de Node.js/Python
   - Revisar logs de build en la plataforma

### **Comandos de Debug:**

```bash
# Ver logs en Railway
railway logs

# Ver logs en Render
# Usar el dashboard web

# Ver logs en Vercel
vercel logs
```

---

## 💰 **Costos Estimados (Planes Gratuitos)**

- **Vercel**: Gratis para proyectos personales
- **Railway**: $5/mes después del trial
- **Render**: Gratis con limitaciones
- **Heroku**: $7/mes por dyno
- **DigitalOcean**: $12/mes mínimo

**Recomendación:** Empieza con Vercel + Railway por su facilidad de uso.
