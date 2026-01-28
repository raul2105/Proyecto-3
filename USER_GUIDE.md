# Guía de Usuario - Flexo Inspection

**Versión**: 1.0  
**Audience**: Operarios, Supervisores, Personal de Calidad  
**Idioma**: Español  

---

## Tabla de Contenidos

1. [Interfaz Principal](#interfaz-principal)
2. [Primeros Pasos (Setup Wizard)](#primeros-pasos-setup-wizard)
3. [Panel de Control](#panel-de-control)
4. [Operación de Inspección](#operación-de-inspección)
5. [Gestión de Recetas](#gestión-de-recetas)
6. [Análisis de Defectos](#análisis-de-defectos)
7. [Reportes](#reportes)
8. [Solución de Problemas](#solución-de-problemas)

---

## Interfaz Principal

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│ FLEXO INSPECTION | Usuario: [admin] | Estado: [●ONLINE]   │
├─────────────────────────────────────────────────────────────┤
│ Menu: │Dashboard│Inspection│Defects│Settings│Reports│      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  SPEED           │  │  [LIVE VIDEO]                │     │
│  │  45.2 m/min      │  │                              │     │
│  └──────────────────┘  │  Master Match: 98%           │     │
│                        │  Registration: OK             │     │
│  ┌──────────────────┐  │                              │     │
│  │  YIELD           │  │  [●] START  [■] STOP        │     │
│  │  99.2 %          │  └──────────────────────────────┘     │
│  └──────────────────┘                                       │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  DEFECTS         │  │  DEFECTOS RECIENTES:         │     │
│  │  0               │  │  • Scratch en (523, 405)     │     │
│  └──────────────────┘  │  • Color shift en (120, 200) │     │
│                        │  • Hole en (800, 150)        │     │
│                        └──────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Estados de Conexión

| Estado | Color | Significado |
|--------|-------|------------|
| **ONLINE** | 🟢 Verde | Sistema listo, Backend responde |
| **OFFLINE** | 🔴 Rojo | Backend no responde, revisar conexión |
| **WARNING** | 🟡 Amarillo | Cámara desconectada o PLC sin respuesta |
| **BUSY** | 🔵 Azul | Procesando, espere... |

---

## Primeros Pasos (Setup Wizard)

El Setup Wizard lo guía paso a paso en la configuración inicial. Se ejecuta automáticamente al primer inicio.

### Paso 1: Seleccionar Cámara

```
┌─ SETUP WIZARD: Paso 1/7 ──────────────────────┐
│                                                 │
│ 🎥 Seleccionar Cámara                         │
│                                                 │
│  ⚪ Virtual Test Camera                        │
│  ⚫ Camera 0  ← Seleccione cámara física      │
│  ⚪ Camera 1                                   │
│                                                 │
│  Exposición: [▁▂▃▄▅▆]  -5.0 EV                │
│                                                 │
│  [← Atrás]  [Siguiente →]                     │
└─────────────────────────────────────────────────┘
```

**Acciones**:
- Seleccionar cámara conectada (verde = conectada)
- Ajustar slider de exposición hasta ver imagen clara
- Clic en "Siguiente"

**Consejos**:
- ✅ Imagen de referencia clara y bien iluminada
- ❌ No muy oscuro (exposición < -8)
- ❌ No muy brillante (exposición > 2)

---

### Paso 2: Cargar Imagen Maestro

```
┌─ SETUP WIZARD: Paso 2/7 ──────────────────────┐
│                                                 │
│ 🖼️ Cargar Imagen Maestro (Referencia)        │
│                                                 │
│  [Seleccionar archivo...]                      │
│  master_reference.pdf                          │
│                                                 │
│  📋 Parámetros PDF:                            │
│  Resolución: [150] DPI                         │
│                                                 │
│  Vista previa:                                  │
│  ┌─────────────────────────────────┐           │
│  │    [Imagen de referencia]        │           │
│  │    Tamaño: 1280 x 720 px         │           │
│  └─────────────────────────────────┘           │
│                                                 │
│  [← Atrás]  [Siguiente →]                     │
└─────────────────────────────────────────────────┘
```

**Acciones**:
- Clic en "Seleccionar archivo"
- Elegir PDF o imagen (JPG, PNG)
- Ajustar DPI si es PDF (150-300 recomendado)
- Clic en "Siguiente"

**Formatos soportados**:
- ✅ PDF (se renderiza a imagen)
- ✅ JPG, PNG (se usan directamente)
- ❌ BMP, GIF (no soportados)

---

### Paso 3: Definir Regiones de Interés (ROIs)

```
┌─ SETUP WIZARD: Paso 3/7 ──────────────────────┐
│                                                 │
│ 🎯 Definir Regiones de Interés (ROIs)         │
│                                                 │
│  Tipo de ROI: [▼ Inspección]                  │
│  (Inspección | Color | Exclusión)             │
│                                                 │
│  Haga clic en la imagen para dibujar:          │
│  ┌──────────────────────────────────────────┐ │
│  │  [Imagen maestro]                        │ │
│  │  Dibuje rectángulo para seleccionar     │ │
│  │  área de inspección                     │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ROIs creados:                                 │
│  ✓ Inspección Area 1 (100x200)                │
│  ✓ Inspección Area 2 (200x150)                │
│                                                 │
│  [+ Añadir ROI]  [← Atrás]  [Siguiente →]    │
└─────────────────────────────────────────────────┘
```

**Acciones**:
1. Seleccionar tipo de ROI en dropdown
2. Dibujar en la imagen: click inicial → arrastra → click final
3. Clic en "+ Añadir ROI" para crear más
4. Clic en "Siguiente"

**Tipos de ROI**:
- **Inspección**: Áreas donde se detectan defectos
- **Color**: Áreas para monitorear color (deltaE)
- **Exclusión**: Áreas a ignorar (marcos, bordes)

---

### Paso 4: Configurar Tolerancias

```
┌─ SETUP WIZARD: Paso 4/7 ──────────────────────┐
│                                                 │
│ ⚙️  Tolerancias de Registro                   │
│                                                 │
│  Posición XY (píxeles):                        │
│  [━━━━━━━━━━•━━━━━━━━]  ±5 px                │
│                                                 │
│  Escala (PPM):                                 │
│  [━━━━━━━━━━•━━━━━━━━]  ±500 ppm             │
│                                                 │
│  Rotación (grados):                            │
│  [━━━━━━━━━━•━━━━━━━━]  ±0.5 °               │
│                                                 │
│  Diferencia de píxeles umbral:                 │
│  [━━━━━━━━━━•━━━━━━━━]  30.0 valores         │
│                                                 │
│  [← Atrás]  [Siguiente →]                     │
└─────────────────────────────────────────────────┘
```

**Acciones**:
- Ajustar sliders según tolerancias requeridas
- Valores más estrictos = más sensibilidad (más alarmas faltas)
- Valores más holgados = menos sensibilidad (pueden pasar defectos)

**Valores recomendados**:
- Posición: ±3-5 px
- Escala: ±500 ppm
- Rotación: ±0.3-0.5 °
- Diferencia: 25-35 valores

---

### Paso 5: Umbrales de Defectos

```
┌─ SETUP WIZARD: Paso 5/7 ──────────────────────┐
│                                                 │
│ 🚨 Umbrales de Detección de Defectos          │
│                                                 │
│  Área mínima (píxeles²):                       │
│  [━━━━━━━━━━•━━━━━━━━]  50 px²               │
│                                                 │
│  Sensibilidad (0-100%):                        │
│  [━━━━━━━━━━•━━━━━━━━]  75 %                 │
│                                                 │
│  Máximo defectos por frame:                    │
│  [━━━━━━━━━━•━━━━━━━━]  3                    │
│                                                 │
│  ⚠️  Previsualizar defectos detectados         │
│  Defectos simulados: 5 detectados              │
│                                                 │
│  [← Atrás]  [Siguiente →]                     │
└─────────────────────────────────────────────────┘
```

**Parámetros**:
- **Área mínima**: Defectos menores a esto se ignoran
- **Sensibilidad**: Mayor = detecta defectos más pequeños
- **Máximo defectos**: Si excede → alarma automática

**Recomendaciones**:
- Material limpio: Área mínima 30-50 px², Sensibilidad 60-75%
- Material sucio: Área mínima 100-150 px², Sensibilidad 40-50%

---

### Paso 6: Configuración de PLC

```
┌─ SETUP WIZARD: Paso 6/7 ──────────────────────┐
│                                                 │
│ 🤖 Conexión a Controlador PLC                 │
│                                                 │
│  Tipo de PLC: [▼ Siemens S7]                 │
│  Opciones: Siemens | Mitsubishi | Allen-Br...│
│                                                 │
│  Configuración de conexión:                    │
│  IP del PLC:  [192.168.1.100]                 │
│  Puerto:      [102]                            │
│  Rack/Slot:   [0/0]                           │
│  Timeout:     [2000] ms                       │
│                                                 │
│  [Probar conexión]  → 🔴 No conectado        │
│                                                 │
│  ℹ️  Si no tiene PLC: marque "Modo simulación"│
│  [✓] Usar simulación de PLC                   │
│                                                 │
│  [← Atrás]  [Siguiente →]                     │
└─────────────────────────────────────────────────┘
```

**Acciones**:
1. Seleccionar tipo de PLC
2. Ingresar IP y puerto
3. Clic en "Probar conexión"
4. Si falla: marcar "Usar simulación" para pruebas
5. Clic en "Siguiente"

---

### Paso 7: Guardar Receta

```
┌─ SETUP WIZARD: Paso 7/7 ──────────────────────┐
│                                                 │
│ 💾 Guardar Configuración como Receta          │
│                                                 │
│  Nombre de receta:  [Cliente A - Trabajo 001]│
│                                                 │
│  Cliente:           [Cliente A]               │
│  Número de trabajo: [001]                     │
│                                                 │
│  ✓ Validación:                                 │
│  ✓ Cámara conectada                           │
│  ✓ Imagen maestro cargada                     │
│  ✓ ROIs definidos (2)                         │
│  ✓ PLC simulado habilitado                    │
│                                                 │
│  [← Atrás]  [Guardar y comenzar]              │
└─────────────────────────────────────────────────┘
```

**Acciones**:
1. Ingresar nombre de receta (único)
2. Verificar validaciones (todas deben estar ✓)
3. Clic en "Guardar y comenzar"

**Resultado**: Sistema comienza inspección automáticamente

---

## Panel de Control

### Dashboard - Vista Principal

```
┌─────────────────────────────────────────────────────────┐
│ FLEXO INSPECTION - DASHBOARD                            │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  INDICADORES PRINCIPALES (KPIs)                     │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │                                                       │ │
│ │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│ │  │ VELOCIDAD  │  │   YIELD    │  │  DEFECTOS  │    │ │
│ │  │ 45.2 m/min │  │  99.2 % ✓  │  │     0      │    │ │
│ │  └────────────┘  └────────────┘  └────────────┘    │ │
│ │                                                       │ │
│ │  ┌─────────────────────────────────────────────┐    │ │
│ │  │  HEATMAP - Ubicación de Defectos            │    │ │
│ │  │  ┌───────────────────────────────────────┐ │    │ │
│ │  │  │                                        │ │    │ │
│ │  │  │  Mapa de distribución de defectos    │ │    │ │
│ │  │  │  Diámetro del rollo: 158.94 mm       │ │    │ │
│ │  │  │                                        │ │    │ │
│ │  │  └───────────────────────────────────────┘ │    │ │
│ │  └─────────────────────────────────────────────┘    │ │
│ │                                                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**KPIs Mostrados**:
- **Velocidad**: Metros/minuto del material
- **Yield**: Porcentaje de material sin defectos críticos
- **Defectos**: Cantidad detectada en tiempo real

**Interactividad**:
- Clic en KPI: Abre detalles
- Hover en Heatmap: Muestra coordenadas

---

## Operación de Inspección

### Iniciar Inspección

```
PANEL DE CONTROL
├─ [●] INSPECCIÓN ACTIVA (En marcha...)
│  ├─ Tiempo: 00:45:23
│  ├─ Imágenes procesadas: 450
│  ├─ Defectos detectados: 3
│  └─ FPS: 15.2
│
├─ [■] DETENER INSPECCIÓN
└─ [⟳] REINICIAR
```

**Pasos**:
1. Cargar receta en dropdown
2. Clic en botón **[●] INICIAR INSPECCIÓN**
3. Sistema comienza captura y análisis
4. Monitor KPIs en tiempo real
5. Clic en **[■] DETENER** para finalizar

**Mientras inspecciona**:
- ✅ Defectos se detectan automáticamente
- ✅ PLC recibe señales en tiempo real
- ✅ Datos se guardan en base de datos
- ✅ Puede revisar defectos en paralelo

---

### Vista de Inspección (Inspection View)

```
┌──────────────────────────────────────────────────┐
│ VISTA DE INSPECCIÓN EN TIEMPO REAL               │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────┐  ┌──────────────────┐  │
│  │    VIVO (Live)     │  │   MAESTRO        │  │
│  │  ┌──────────────┐  │  │  ┌────────────┐ │  │
│  │  │              │  │  │  │            │ │  │
│  │  │[Video stream]│  │  │  │[Reference] │ │  │
│  │  │              │  │  │  │            │ │  │
│  │  └──────────────┘  │  │  └────────────┘ │  │
│  │                    │  │                  │  │
│  │  FPS: 15.2         │  │ Registro: OK    │  │
│  │  Lag: 45ms         │  │ Coincidencia: 98%  │
│  └────────────────────┘  └──────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │    HEATMAP - Puntuación de Diferencia      │ │
│  │  ┌────────────────────────────────────────┐ │ │
│  │  │                                        │ │ │
│  │  │ [Diferencias color-codificadas]       │ │ │
│  │  │ Verde: OK | Amarillo: Leve            │ │ │
│  │  │ Rojo: DEFECTO                         │ │ │
│  │  │                                        │ │ │
│  │  └────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [Opciones de vista: ◻ Vivo  ◻ Maestro  ◼ Diff] │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Indicadores**:
- 🟢 **Vivo**: Stream en tiempo real de cámara
- 🔵 **Maestro**: Imagen de referencia cargada
- 🟣 **Heatmap**: Diferencias visualizadas

---

## Gestión de Recetas

### Crear Receta Nueva

```
MENU → SETTINGS → RECETAS
│
├─ [+ NUEVA RECETA]
│  ├─ Nombre: [Customer A - Job 001]
│  ├─ Cliente: [Customer A]
│  ├─ Cargar maestro: [Seleccionar...]
│  ├─ Tolerancias: [Editar...]
│  ├─ Defect Thresholds: [Editar...]
│  └─ [Guardar]
│
└─ ✓ Receta creada exitosamente
```

### Clonar Receta Existente

```
MENÚ → RECETA
│
├─ [Cliente A - Trabajo 001]  [▼ Opciones]
│  ├─ Editar
│  ├─ Clonar
│  ├─ Borrar
│  └─ Ver historial
│
├─ [Clonar]
│  ├─ Nombre nueva: [Cliente A - Trabajo 002]
│  └─ [✓ Crear copia]
│
└─ ✓ Receta clonada
```

### Gestión de Recetas

```
MENÚ → CONFIGURACIÓN → GESTOR DE RECETAS
┌────────────────────────────────────────┐
│ RECETAS DISPONIBLES:                   │
├────────────────────────────────────────┤
│                                        │
│ ✓ Cliente A - Trabajo 001              │
│   Última uso: Hoy 09:30                │
│   Defectos promedio: 0.5 por rollo    │
│   [Editar] [Clonar] [Borrar]          │
│                                        │
│ ✓ Cliente A - Trabajo 002              │
│   Última uso: Ayer 14:15               │
│   Defectos promedio: 0.3 por rollo    │
│   [Editar] [Clonar] [Borrar]          │
│                                        │
│ ✓ Cliente B - Trabajo 001              │
│   Última uso: 2 días atrás             │
│   Defectos promedio: 1.2 por rollo    │
│   [Editar] [Clonar] [Borrar]          │
│                                        │
│ [+ Nueva Receta]                      │
│                                        │
└────────────────────────────────────────┘
```

---

## Análisis de Defectos

### Explorador de Defectos

```
MENÚ → DEFECTOS
┌────────────────────────────────────────────┐
│ EXPLORADOR DE DEFECTOS                     │
├────────────────────────────────────────────┤
│                                            │
│ Filtros:                                   │
│ Tipo: [Todos ▼]  Severidad: [Todos ▼]    │
│ Fecha: [Hoy ▼]    Estado: [Todos ▼]      │
│                                            │
│ RESULTADOS: 15 defectos encontrados       │
│                                            │
│ ┌──────────────────────────────────────┐  │
│ │ ID    │ Tipo    │ Severidad │ ROI   │ │
│ ├──────────────────────────────────────┤  │
│ │ D001  │ Scratch │ CRÍTICO   │ Area1 │ │
│ │ D002  │ Hole    │ MAYOR     │ Area2 │ │
│ │ D003  │ Color   │ MENOR     │ Area1 │ │
│ │ D004  │ Scratch │ MAYOR     │ Area3 │ │
│ │ ...   │ ...     │ ...       │ ...   │ │
│ └──────────────────────────────────────┘  │
│                                            │
│ Seleccione defecto para ver detalles       │
│                                            │
└────────────────────────────────────────────┘
```

### Detalle de Defecto

```
DEFECTO: D001
┌────────────────────────────────────────────┐
│ INFORMACIÓN DEL DEFECTO                    │
├────────────────────────────────────────────┤
│                                            │
│ Tipo: Scratch (Rayadura)                  │
│ Severidad: CRÍTICO 🔴                      │
│ Área: 520 px²                              │
│ Posición: (523, 405)                      │
│ Timestamp: 2026-01-23 10:45:32            │
│ ROI: Area de Inspección 1                 │
│                                            │
│ ┌──────────────────────────────────────┐  │
│ │  [VIVO]  [MAESTRO]  [HEATMAP]        │  │
│ │                                      │  │
│ │  ┌────────────────────────────────┐ │  │
│ │  │                                 │ │  │
│ │  │     [Imagen del defecto]        │ │  │
│ │  │     Con círculo rojo indicando  │ │  │
│ │  │     la ubicación                │ │  │
│ │  │                                 │ │  │
│ │  └────────────────────────────────┘ │  │
│ │                                      │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Acciones de Alarma Asociadas:             │
│ • Torre Roja: Encendida                   │
│ • Buzzer: 500ms                           │
│ • Parada de línea: Solicitada             │
│ • Marcado de segmento: Sí                 │
│                                            │
│ [Descargar evidencia]  [Aceptar]  [Cerrar]│
│                                            │
└────────────────────────────────────────────┘
```

---

## Reportes

### Historial de Trabajos

```
MENÚ → REPORTES
┌──────────────────────────────────────────┐
│ REPORTES Y TRAZABILIDAD                  │
├──────────────────────────────────────────┤
│                                          │
│ TRABAJOS COMPLETADOS:                   │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Trabajo  │ Fecha      │ Defectos │ │
│ ├────────────────────────────────────┤  │
│ │ J001     │ 23 Ene    │    3     │ │
│ │ J002     │ 22 Ene    │    1     │ │
│ │ J003     │ 21 Ene    │    8     │ │
│ │ ...      │ ...       │   ...    │ │
│ └────────────────────────────────────┘  │
│                                          │
│ [Exportar a PDF]  [Exportar a Excel]    │
│                                          │
└──────────────────────────────────────────┘
```

### Reporte Detallado de Trabajo

```
REPORTE DE TRABAJO: J001
┌──────────────────────────────────────────────┐
│ INFORMACIÓN GENERAL                          │
├──────────────────────────────────────────────┤
│ Trabajo ID: J001                             │
│ Cliente: Customer A                          │
│ Receta: Customer A - Job 001                 │
│ Operario: Juan García                        │
│ Fecha: 23 Enero 2026                         │
│ Hora: 09:30 - 11:45                          │
│ Duración: 2h 15min                           │
│                                              │
│ ESTADÍSTICAS:                                │
├──────────────────────────────────────────────┤
│ Material procesado: 1,350 metros             │
│ Velocidad promedio: 45.2 m/min               │
│ Total rollos: 2                              │
│ Defectos encontrados: 3                      │
│ Yield: 99.2%                                 │
│                                              │
│ DEFECTOS POR TIPO:                           │
│ • Scratch: 1 (crítico)                       │
│ • Hole: 1 (mayor)                            │
│ • Color Shift: 1 (menor)                     │
│                                              │
│ EVENTOS REGISTRADOS:                         │
│ • 09:32 - Inspección iniciada               │
│ • 10:15 - Alarma crítica #1                 │
│ • 10:47 - Parada de línea (5 segundos)      │
│ • 11:32 - Alarma mayor #2                   │
│ • 11:45 - Inspección completada             │
│                                              │
│ [Descargar PDF]  [Enviar por email]  [Cerrar]│
│                                              │
└──────────────────────────────────────────────┘
```

---

## Solución de Problemas

### P: "Sistema muestra OFFLINE"

**R**: 
1. Verificar que Backend está ejecutándose (Terminal debe estar abierta)
2. Esperar 10 segundos (puede estar reiniciando)
3. Presionar F5 para refrescar navegador
4. Si persiste: Cerrar el script RUN_APP.bat y ejecutar nuevamente

---

### P: "Cámara no captura"

**R**:
1. Ir a SETTINGS → CAMERA
2. Seleccionar "Virtual Test Camera" (para probar sin cámara)
3. Si tiene cámara USB: Verificar que esté conectada
4. Probar en Windows: Settings → Devices → Cameras

---

### P: "Defectos no se detectan"

**R**:
1. Revisar que imagen maestro está bien cargada
2. Ajustar sensibilidad en Settings (mayor = más sensible)
3. Verificar área mínima de defecto (no muy alta)
4. Revisar iluminación de cámara (no muy oscuro)

---

### P: "PLC no recibe señales"

**R**:
1. Verificar IP del PLC es correcta
2. Ping a PLC desde terminal: `ping 192.168.1.100`
3. Revisar firewall permite puerto (102, 502, etc)
4. En Settings → PLC: Marcar "Usar simulación" para pruebas

---

### P: "¿Cómo exportar reportes?"

**R**:
1. Ir a MENU → REPORTES
2. Seleccionar trabajo
3. Clic en "Exportar a PDF" o "Exportar a Excel"
4. Archivo se descarga automáticamente

---

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `F1` | Abrir ayuda |
| `Space` | Iniciar/Detener inspección |
| `R` | Reiniciar inspección |
| `D` | Abrir explorador de defectos |
| `S` | Abrir Settings |
| `Esc` | Cerrar diálogos |
| `Ctrl+S` | Guardar configuración |

---

**Última actualización**: 23 de Enero de 2026  
**Versión**: 1.0
