# Mejoras de Código - Implementación Rápida

**Versión**: 1.0  
**Fecha**: 23 de Enero de 2026  
**Objetivo**: Mejoras implementables en el código actual (backends + frontend)  

---

## Tabla de Contenidos

1. [Backend - Mejoras Críticas](#backend---mejoras-críticas)
2. [Frontend - Mejoras UX](#frontend---mejoras-ux)
3. [Seguridad - Fixes Inmediatos](#seguridad---fixes-inmediatos)
4. [Performance - Optimizaciones](#performance---optimizaciones)
5. [Testing - Cobertura](#testing---cobertura)

---

## Backend - Mejoras Críticas

### 1. Agregar Logging Adecuado

**Problema**: No hay logging centralizado, solo prints.

**Solución**:
```python
# backend/logger.py (nuevo archivo)
import logging
import logging.handlers
from pathlib import Path

# Crear directorio logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configurar logger
logger = logging.getLogger("flexo_inspection")
logger.setLevel(logging.DEBUG)

# Handler para archivo
file_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
```

**Uso en main.py**:
```python
from logger import logger

@app.post("/login")
def login(req: LoginRequest):
    try:
        result = state.auth_service.login(req)
        logger.info(f"User {req.username} logged in successfully")
        return result
    except Exception as e:
        logger.error(f"Login failed for user {req.username}: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
```

**Esfuerzo**: 2 horas  
**Impacto**: Alto - Debugging y auditoría

---

### 2. Agregar Health Check Endpoint

**Problema**: No hay forma de verificar que el sistema está sano.

**Solución**:
```python
# backend/main.py
@app.get("/health")
async def health_check():
    """
    Endpoint de health check para monitoring
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "camera": "connected" if state.camera.cap else "disconnected",
                "database": "ok" if state.trace_entries else "initializing",
                "plc": "connected" if state.plc_connected else "disconnected",
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            }
        }
        
        # Verificar métricas críticas
        if health_status["services"]["cpu_percent"] > 90:
            health_status["status"] = "warning"
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

**Requiere**: `pip install psutil`

**Esfuerzo**: 1 hora  
**Impacto**: Medio - Monitoring

---

### 3. Mejorar Manejo de Excepciones

**Problema**: Excepciones genéricas, sin contexto.

**Solución**:
```python
# backend/exceptions.py (nuevo archivo)
from fastapi import HTTPException

class FlexoException(Exception):
    """Base exception para Flexo Inspection"""
    pass

class CameraException(FlexoException):
    """Camera connection/capture errors"""
    pass

class RegistrationFailedException(FlexoException):
    """Image registration failed"""
    pass

class DefectDetectionException(FlexoException):
    """Defect detection errors"""
    pass

class PLCException(FlexoException):
    """PLC communication errors"""
    pass

class RecipeException(FlexoException):
    """Recipe loading/validation errors"""
    pass

# Middleware para capturar excepciones
@app.exception_handler(FlexoException)
async def flexo_exception_handler(request, exc):
    logger.error(f"Flexo error: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "error_type": type(exc).__name__}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": str(uuid.uuid4())}
    )
```

**Uso**:
```python
@app.get("/cameras")
async def list_cameras():
    try:
        cameras = state.camera.list_cameras()
        if not cameras:
            raise CameraException("No cameras found")
        return cameras
    except CameraException as e:
        raise  # Caught by exception handler
```

**Esfuerzo**: 2 horas  
**Impacto**: Alto - Debugging y UX

---

### 4. Agregar Validación de Input

**Problema**: Falta validación de datos entrantes.

**Solución**:
```python
# backend/main.py - Mejorar validaciones Pydantic

class DefectThresholds(BaseModel):
    min_area: float = Field(..., gt=0, le=10000)
    sensitivity: float = Field(..., ge=0, le=100)

class AlarmRules(BaseModel):
    critical_defect_area: float = Field(..., gt=0)
    defect_rate_per_frame: int = Field(..., gt=0, le=100)
    brightness_min: float = Field(..., ge=0, le=255)
    brightness_max: float = Field(..., ge=0, le=255)
    
    @validator('brightness_max')
    def brightness_max_greater_than_min(cls, v, values):
        if v <= values.get('brightness_min', 0):
            raise ValueError('brightness_max debe ser > brightness_min')
        return v

class Recipe(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    client: str = Field(..., max_length=100)
    exposure: float = Field(..., ge=-10, le=10)
    tolerances: Dict[str, float]
    defect_thresholds: DefectThresholds
```

**Esfuerzo**: 1 hora  
**Impacto**: Medio - Seguridad

---

### 5. Agregar Rate Limiting

**Problema**: Sin protección contra abuso de API.

**Solución**:
```bash
pip install slowapi
```

```python
# backend/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"}
    )

@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest):
    """Máximo 5 intentos por minuto"""
    # ...

@app.get("/inspection-frame")
@limiter.limit("30/minute")
def get_inspection_frame(request: Request):
    """Máximo 30 frames por minuto"""
    # ...
```

**Esfuerzo**: 1 hora  
**Impacto**: Alto - Seguridad

---

## Frontend - Mejoras UX

### 1. Agregar Error Boundary

**Problema**: Si un componente falla, toda la app se rompe.

**Solución**:
```jsx
// frontend/src/components/ErrorBoundary.jsx
import React from 'react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo)
    // Aquí podrías enviar a un servicio de logging
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h1>⚠️ Algo salió mal</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Recargar aplicación
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

// En App.jsx
<ErrorBoundary>
  {/* Contenido principal */}
</ErrorBoundary>
```

**Esfuerzo**: 1 hora  
**Impacto**: Medio - Resiliencia

---

### 2. Agregar Componente de Notificaciones

**Problema**: Las alarmas se pierden si no está viendo el panel.

**Solución**:
```jsx
// frontend/src/components/NotificationCenter.jsx
import { useEffect, useState } from 'react'

const notificationStyles = {
  error: { background: '#dc3545', color: 'white' },
  warning: { background: '#ffc107', color: 'black' },
  success: { background: '#28a745', color: 'white' },
  info: { background: '#17a2b8', color: 'white' }
}

export function Toast({ id, type, message, duration, onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => onClose(id), duration)
    return () => clearTimeout(timer)
  }, [id, duration, onClose])

  return (
    <div 
      className="toast" 
      style={notificationStyles[type]}
    >
      {message}
      <button onClick={() => onClose(id)}>✕</button>
    </div>
  )
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState([])

  const addNotification = (message, type = 'info', duration = 3000) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, message, type, duration }])
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  useEffect(() => {
    // Exponer globalmente para que otros componentes puedan usarlo
    window.notify = addNotification
  }, [])

  return (
    <div className="notification-stack">
      {notifications.map(notif => (
        <Toast
          key={notif.id}
          {...notif}
          onClose={removeNotification}
        />
      ))}
    </div>
  )
}

// Uso en cualquier componente:
// window.notify('Alarma crítica detectada', 'error', 5000)
```

**CSS adicional**:
```css
.notification-stack {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  padding: 15px 20px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 300px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

**Esfuerzo**: 2 horas  
**Impacto**: Alto - UX

---

### 3. Agregar Loading States

**Problema**: Usuario no sabe si algo se está procesando.

**Solución**:
```jsx
// frontend/src/hooks/useAsync.js
import { useState, useEffect } from 'react'

export function useAsync(asyncFunction, immediate = true) {
  const [status, setStatus] = useState('idle') // idle | pending | success | error
  const [value, setValue] = useState(null)
  const [error, setError] = useState(null)

  const execute = async () => {
    setStatus('pending')
    setValue(null)
    setError(null)
    try {
      const response = await asyncFunction()
      setValue(response)
      setStatus('success')
      return response
    } catch (error) {
      setError(error)
      setStatus('error')
      throw error
    }
  }

  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [])

  return { execute, status, value, error }
}

// Uso
export function CameraSettings() {
  const { status, value: cameras } = useAsync(() => 
    fetch('/cameras').then(r => r.json())
  )

  return (
    <div>
      {status === 'pending' && <p>Cargando cámaras...</p>}
      {status === 'error' && <p className="error">Error al cargar</p>}
      {status === 'success' && (
        <select>
          {cameras?.map(cam => (
            <option key={cam.id} value={cam.id}>{cam.name}</option>
          ))}
        </select>
      )}
    </div>
  )
}
```

**Esfuerzo**: 2 horas  
**Impacto**: Medio - UX

---

### 4. Agregar Cancelación de Requests

**Problema**: Requests viejos pueden sobrescribir data más reciente.

**Solución**:
```jsx
// frontend/src/hooks/useFetch.js
import { useEffect, useState, useRef } from 'react'

export function useFetch(url) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    // Cancelar request anterior si existe
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    const fetchData = async () => {
      try {
        setLoading(true)
        const res = await fetch(url, {
          signal: abortControllerRef.current.signal
        })
        const json = await res.json()
        setData(json)
        setError(null)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // Cleanup: cancelar request al desmontar
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [url])

  return { data, loading, error }
}

// Uso
export function Dashboard() {
  const { data: stats, loading } = useFetch('/api/stats')

  return loading ? <p>Cargando...</p> : <StatsDisplay stats={stats} />
}
```

**Esfuerzo**: 2 horas  
**Impacto**: Medio - Performance

---

## Seguridad - Fixes Inmediatos

### 1. Agregar HTTPS en Producción

**backend/main.py**:
```python
if not DEBUG:  # En producción
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["inspection.company.com"]
    )
    
    # Force HTTPS
    @app.middleware("http")
    async def force_https(request, call_next):
        if request.url.scheme != "https":
            return RedirectResponse(
                url=request.url.replace(scheme="https"),
                status_code=307
            )
        return await call_next(request)
```

---

### 2. Agregar HSTS Header

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

### 3. Proteger Variables Sensibles

**backend/.env.example**:
```
DATABASE_URL=sqlite:///./data/inspect.db
SECRET_KEY=your-super-secret-key-here
DEBUG=false
JWT_EXPIRATION_HOURS=8
CORS_ORIGINS=https://inspection.company.com
```

**backend/main.py**:
```python
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if not DEBUG:
    print("Running in PRODUCTION mode")
```

**Esfuerzo**: 1 hora  
**Impacto**: Crítico - Seguridad

---

## Performance - Optimizaciones

### 1. Agregar Caché a Endpoints Estáticos

```python
# backend/main.py
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Caché de 1 hora para assets estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/recipes/{name}")
async def get_recipe(name: str):
    """Caché 5 minutos"""
    # En producción, usar Redis
    @cache(expire=300)  # 5 minutos
    def _get_recipe():
        return state.recipe_manager.load_recipe(name)
    
    return _get_recipe()
```

**Requiere**: `pip install cachetools`

---

### 2. Agregar Paginación a Endpoints de Lista

```python
# backend/main.py
from pydantic import BaseModel

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50
    
    @validator('limit')
    def limit_max(cls, v):
        return min(v, 100)  # Máximo 100

@app.get("/defects")
async def get_defects(skip: int = 0, limit: int = 50):
    """
    Devuelve defectos con paginación
    
    Query params:
    - skip: cuántos saltar (default 0)
    - limit: máximo a devolver (max 100)
    """
    all_defects = list(state.defect_events)
    total = len(all_defects)
    
    defects = all_defects[skip:skip+limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": defects
    }
```

---

### 3. Comprimir Respuestas

```python
# backend/main.py
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Esto comprime respuestas > 1KB automáticamente
```

**Beneficio**: ~70% reducción en tamaño de payload

---

## Testing - Cobertura

### 1. Agregar Tests Básicos

```bash
pip install pytest pytest-asyncio
```

**backend/test_auth.py**:
```python
from fastapi.testclient import TestClient
from main import app, state

client = TestClient(app)

def test_login_success():
    response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_fail():
    response = client.post("/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "warning"]
```

**Ejecutar**:
```bash
pytest backend/ -v --cov=backend
```

**Esfuerzo**: 3 horas  
**Impacto**: Medio - Calidad

---

## Resumen de Prioridades

```
CRÍTICO (Semana 1):
✓ Rate limiting
✓ Seguridad (HTTPS, headers)
✓ Validación de input
✓ Logging

IMPORTANTE (Semana 2):
✓ Error handling mejorado
✓ Health check
✓ Notificaciones frontend
✓ Error boundary

OPTIMIZACIÓN (Semana 3):
✓ Caché
✓ Paginación
✓ Compresión
✓ Tests básicos
```

---

**Última actualización**: 23 de Enero de 2026  
**Versión**: 1.0
