# Manual de Instalación y Configuración - Flexo Inspection

**Versión**: 1.0  
**Fecha**: 23 de Enero de 2026  
**Sistema Operativo**: Windows 10/11  

---

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Base](#instalación-base)
3. [Configuración Inicial](#configuración-inicial)
4. [Integración con PLC](#integración-con-plc)
5. [Validación de Instalación](#validación-de-instalación)
6. [Solución de Problemas](#solución-de-problemas)
7. [Actualización y Mantenimiento](#actualización-y-mantenimiento)

---

## Requisitos Previos

### Hardware Recomendado
- **CPU**: Intel i7/i9 o equivalente AMD Ryzen 7+
- **RAM**: 16 GB mínimo (32 GB recomendado)
- **SSD**: 256 GB (para almacenar evidencia de imágenes)
- **Cámara Industrial**: USB 3.0 (resolución mínima 1280x720)
- **Conexión de Red**: Ethernet (para comunicación PLC)

### Software Requerido

#### 1. Python 3.10+
```powershell
# Descargar desde: https://www.python.org/downloads/
# Instalación: incluir "Add Python to PATH"

# Verificar instalación
python --version  # Debe mostrar Python 3.10+
pip --version
```

#### 2. Node.js 18+
```powershell
# Descargar desde: https://nodejs.org/
# LTS version recomendada

# Verificar instalación
node --version
npm --version
```

#### 3. Git (Opcional pero recomendado)
```powershell
# Descargar desde: https://git-scm.com/download/win
```

---

## Instalación Base

### Paso 1: Clonar/Descargar Proyecto

```powershell
# Opción A: Con Git
git clone <repositorio-url>
cd Proyecto-3

# Opción B: Descargar ZIP
# - Descargar proyecto
# - Extraer en carpeta deseada
# - Abrir PowerShell en la carpeta
```

### Paso 2: Crear Entorno Virtual Python

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno
.venv\Scripts\Activate.ps1

# Si recibe error de política de ejecución:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Luego intente nuevamente
```

### Paso 3: Instalar Dependencias Backend

```powershell
# Asegúrese que el entorno virtual está activado
# El prompt debe mostrar: (.venv) C:\...>

# Instalar dependencias
pip install -r backend/requirements.txt

# Instalar dependencias adicionales (Opcional)
pip install pytest black flake8  # Testing y linting
```

### Paso 4: Instalar Dependencias Frontend

```powershell
# Navegar a carpeta frontend
cd frontend

# Instalar dependencias npm
npm install

# Volver a carpeta raíz
cd ..
```

### Paso 5: Crear Carpetas de Datos

```powershell
# Crear estructura de directorios
New-Item -ItemType Directory -Force -Path backend\data
New-Item -ItemType Directory -Force -Path backend\evidence
New-Item -ItemType Directory -Force -Path backend\recipes
New-Item -ItemType Directory -Force -Path frontend\public\uploads
```

---

## Configuración Inicial

### Configuración Backend (config.json)

Editar `backend\config.json`:

```json
{
  "settings": {
    "use_simulator": true,           # true para pruebas sin cámara
    "camera_id": 1,                  # ID de cámara (0, 1, 2...)
    "exposure": -5.0,                # Exposición (-10 a 10)
    "gain": null,                    # Ganancia (null = automático)
    "roll_diameter_mm": 158.94,      # Diámetro del rollo
    "core_diameter_mm": 76.0,        # Diámetro del núcleo
    "material_thickness_mm": 0.05,   # Espesor del material
    "start_with_last_job": false     # Retomar último trabajo
  },
  "retention_policy": {
    "thumbnails_days": 30,           # Retener miniaturas (días)
    "evidence_days": 90,             # Retener evidencia (días)
    "video_days": 14                 # Retener video (días)
  },
  "alarm_rules": {
    "critical_defect_area": 500.0,   # Área mínima crítica (px²)
    "defect_rate_per_frame": 3,      # Máximo defectos por frame
    "brightness_min": 10.0,          # Mínimo brillo (0-255)
    "brightness_max": 245.0          # Máximo brillo (0-255)
  },
  "sensor_config": {
    "label_pitch_m": 0.0,            # Distancia entre etiquetas
    "cmark_enabled": false,          # Marca de control habilitada
    "jitter_tolerance_ms": 20,       # Tolerancia de jitter
    "fallback_encoder": true,        # Usar encoder como fallback
    "encoder_pitch_m": 0.0,          # Distancia por pulso
    "mm_per_tick": 0.0,              # Milímetros por pulso
    "repeat_mm": 0.0                 # Patrón de repetición
  }
}
```

### Variables de Entorno Frontend (opcional)

Crear `.env.local` en carpeta `frontend`:

```
VITE_API_URL=http://127.0.0.1:8001
VITE_API_TIMEOUT=5000
VITE_DEBUG_MODE=false
```

---

## Integración con PLC

### Opción A: Siemens S7-1200/1500

#### Requisitos:
- PLC con Ethernet (módulo de comunicación)
- IP PLC: ej. `192.168.1.100`
- Puerto: `102` (RFC 1006)

#### Instalación de Bibliotecas:
```powershell
pip install python-snap7
```

#### Configuración (backend/main.py):
```python
from snap7 import snap7

# Conexión
plc = snap7.client.Client()
plc.connect('192.168.1.100', 0, 0, 102)

# Enviar señal (escribir en variable booleana)
# DB1.DBX0.0 = Stop Line
plc.db_write(1, 0, bytearray([0x01]))
```

#### Ejemplo de Receta Siemens:
```
NETWORK 1 "Recibir Alarma"
  LD  M 0.0          // Alarma detectada
  AN  M 0.1          // No en cooldown
  S   M 2.0          // Set Stop Line
  S   M 2.1          // Set Tower Red
  
NETWORK 2 "Cooldown"
  LD  M 2.0
  TON T 1, 0.2       // Timer 200ms
  R   M 2.0
```

---

### Opción B: Mitsubishi FX/Q Series

#### Requisitos:
- PLC con módulo Ethernet
- IP PLC: ej. `192.168.1.101`
- Puerto: `502` (Modbus TCP)

#### Instalación de Bibliotecas:
```powershell
pip install pymodbus
```

#### Configuración (backend/main.py):
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.101', port=502)

# Enviar señal (coil en dirección 100)
client.write_coil(100, True)  # Stop Line
client.write_coil(101, True)  # Tower Red
```

#### Direcciones Modbus Mitsubishi:
```
Coil (Salida)     | Dirección | Función
Stop Line         | Y000      | 0100 (M)
Tower Red         | Y001      | 0101 (M)
Tower Yellow      | Y002      | 0102 (M)
Buzzer            | Y003      | 0103 (M)
Mark Segment      | Y004      | 0104 (M)
```

---

### Opción C: Allen-Bradley CompactLogix

#### Requisitos:
- PLC CompactLogix L30 o superior
- Módulo EtherNet/IP
- IP PLC: ej. `192.168.1.102`
- Puerto: `2222`

#### Instalación de Bibliotecas:
```powershell
pip install pycomm3
```

#### Configuración (backend/main.py):
```python
from pycomm3 import LogixDriver

with LogixDriver('192.168.1.102') as plc:
    # Enviar señal
    plc.write(('StopLine', True))
    plc.write(('TowerRed', True))
    
    # Leer estado
    status = plc.read('PLC_Status')
```

---

### Opción D: Keyence

#### Requisitos:
- PLC Keyence KV-7000 o superior
- Módulo Ethernet/IP
- IP PLC: ej. `192.168.1.103`
- Puerto: `502` (Modbus TCP)

#### Instalación de Bibliotecas:
```powershell
pip install pymodbus
```

#### Configuración (backend/main.py):
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.103', port=502)

# Keyence utiliza Modbus TCP estándar
client.write_coil(100, True)  # Stop Line
```

---

### Configuración de PLC en config.json

Agregar sección a `backend/config.json`:

```json
"plc_config": {
  "type": "siemens",              # siemens | mitsubishi | allen_bradley | keyence
  "ip": "192.168.1.100",
  "port": 102,
  "rack": 0,                      # Siemens: rack/slot
  "slot": 0,
  "timeout_ms": 2000,
  "retry_attempts": 3,
  "retry_delay_ms": 100,
  
  "signals": {
    "stop_line": {
      "type": "coil",             # coil | register | digital
      "address": 0,               # Dirección en PLC
      "duration_ms": 1000
    },
    "tower_red": {
      "type": "coil",
      "address": 1,
      "duration_ms": 500
    },
    "buzzer": {
      "type": "coil",
      "address": 2,
      "duration_ms": 500
    }
  }
}
```

---

## Validación de Instalación

### Prueba 1: Verificar Python y Dependencias

```powershell
# En carpeta raíz del proyecto
.venv\Scripts\Activate.ps1

# Verificar dependencias
pip list

# Salida esperada (parcial):
# FastAPI              0.x.x
# uvicorn              0.x.x
# opencv-python        4.x.x
# numpy                1.x.x
# Pillow               9.x.x
```

### Prueba 2: Verificar Node.js

```powershell
cd frontend
npm list

# Salida esperada (parcial):
# react@19.2.0
# react-dom@19.2.0
# vite@7.2.4
# recharts@3.7.0
```

### Prueba 3: Iniciar Aplicación

**Opción A: Usar Script RUN_APP.bat (Automático)**

```powershell
# Desde carpeta raíz
.\RUN_APP.bat

# Debería:
# 1. Activar entorno virtual
# 2. Iniciar Backend en puerto 8001
# 3. Iniciar Frontend en puerto 5173
# 4. Abrir navegador en http://localhost:5173
```

**Opción B: Inicio Manual (Para debugging)**

Terminal 1 (Backend):
```powershell
.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Terminal 2 (Frontend):
```powershell
cd frontend
npm run dev
```

Terminal 3 (Navegador):
```powershell
start http://localhost:5173
```

### Prueba 4: Validar Conectividad

```powershell
# Verificar Backend
curl http://127.0.0.1:8001/docs

# Verificar Frontend
curl http://127.0.0.1:5173

# Verificar cámara (en terminal Backend)
# Debe mostrar lista de cámaras disponibles
```

### Prueba 5: Login de Prueba

Credenciales por defecto (en backend/auth.py):

| Usuario | Contraseña | Rol        |
|---------|-----------|-----------|
| admin   | admin123  | admin     |
| op1     | 1234      | operator  |
| sup1    | sup123    | supervisor|
| qual1   | qual123   | quality   |

---

## Solución de Problemas

### Problema: "Python no reconocido"

```powershell
# Verificar instalación
python --version

# Si no funciona, reinstalar Python
# - Descargar de https://www.python.org/downloads/
# - IMPORTANTE: Marcar "Add Python to PATH" durante instalación

# Verificar PATH
$env:PATH

# Si aún no funciona, agregar manualmente:
$env:PATH += ";C:\Users\<usuario>\AppData\Local\Programs\Python\Python310"
```

### Problema: "Command 'npm' not found"

```powershell
# Reinstalar Node.js desde https://nodejs.org/
# O agregar a PATH:
$env:PATH += ";C:\Program Files\nodejs"
```

### Problema: "No module named 'fastapi'"

```powershell
# Verificar que entorno virtual está activado
# El prompt debe mostrar: (.venv) C:\...>

# Si no está activado:
.venv\Scripts\Activate.ps1

# Reinstalar dependencias
pip install -r backend/requirements.txt
```

### Problema: "Backend no inicia (Port 8001 in use)"

```powershell
# Encontrar proceso usando puerto 8001
Get-NetTCPConnection -LocalPort 8001

# Matar proceso (reemplazar PID)
Stop-Process -Id <PID> -Force

# O cambiar puerto en backend/main:
# uvicorn.run(app, host="0.0.0.0", port=8002)
```

### Problema: "Frontend no ve Backend (API error)"

```powershell
# 1. Verificar Backend está corriendo:
curl http://127.0.0.1:8001/docs

# 2. Verificar CORS en backend/main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ojo: Cambiar en producción
    ...
)

# 3. Si VITE_API_URL mal configurado:
# Editar frontend/.env.local
VITE_API_URL=http://127.0.0.1:8001
```

### Problema: "Cámara no se conecta"

```powershell
# Verificar cámaras disponibles
cd backend
python -c "
import cv2
from camera import CameraService
cs = CameraService()
print(cs.list_cameras())
"

# Si no detecta: usar simulator en config.json
# "use_simulator": true

# Para probar con cámara USB:
# 1. Conectar cámara USB
# 2. Abrir Administrador de dispositivos
# 3. Buscar "USB Video Device"
# 4. Nota el ID (generalmente 0 ó 1)
```

### Problema: "PLC no conecta"

```powershell
# 1. Verificar IP y puerto
ping 192.168.1.100

# 2. Probar conexión
python -c "
from snap7 import snap7
plc = snap7.client.Client()
plc.connect('192.168.1.100', 0, 0, 102)
print('Conectado!' if plc.get_connected() else 'No conectado')
"

# 3. Verificar firewall permite puerto (102, 502, 2222)
# Control Panel > Windows Defender Firewall > Allow app through firewall

# 4. Verificar cables Ethernet
```

---

## Actualización y Mantenimiento

### Actualizar Dependencias Python

```powershell
.venv\Scripts\Activate.ps1

# Verificar actualizaciones disponibles
pip list --outdated

# Actualizar todas (arriesgado)
pip install --upgrade -r backend/requirements.txt

# Actualizar paquete específico (seguro)
pip install --upgrade fastapi uvicorn
```

### Actualizar Dependencias Frontend

```powershell
cd frontend

# Verificar actualizaciones
npm outdated

# Actualizar todo
npm update

# O actualizar paquete específico
npm install react@latest
```

### Backup de Datos

```powershell
# Crear backup de base de datos y recetas
$BackupDir = "backups\$(Get-Date -Format 'yyyy-MM-dd_HHmm')"
New-Item -ItemType Directory -Path $BackupDir

# Copiar archivos importantes
Copy-Item -Path backend\data\* -Destination $BackupDir -Recurse
Copy-Item -Path backend\recipes\* -Destination $BackupDir -Recurse
Copy-Item -Path backend\config.json -Destination $BackupDir

Write-Host "Backup creado en: $BackupDir"
```

### Limpiar Cache

```powershell
# Limpiar caché Python
Remove-Item -Recurse -Force backend\__pycache__
Remove-Item -Recurse -Force frontend\node_modules\.cache

# Limpiar build
Remove-Item -Recurse -Force frontend\dist

# Rebuilt
cd frontend
npm run build
```

---

## Próximos Pasos

1. **Configurar PLC**: Elegir opción (A, B, C o D) e integrar
2. **Cargar Recetas**: Usar SetupWizard para crear recetas
3. **Calibrar Cámara**: Ajustar exposición, ROIs
4. **Pruebas de Alarma**: Verificar señales PLC
5. **Capacitar Operarios**: Usar manual de operación

---

## Contacto y Soporte

- **Documentación Técnica**: Ver `ARCHITECTURE.md`
- **Guía de Usuario**: Ver `USER_GUIDE.md`
- **API Docs**: http://localhost:8001/docs (cuando backend está corriendo)
- **Issues**: Crear ticket en repositorio

---

**Última actualización**: 23 de Enero de 2026  
**Versión**: 1.0
