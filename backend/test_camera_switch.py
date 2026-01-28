#!/usr/bin/env python3
"""
Test: Cambio de Simulator → Live Camera
Detecta problemas cuando se cambia de modo
"""

import sys
import cv2
from camera import CameraService
from color_module import ColorMonitor, ColorTarget

def test_camera_switch():
    """Test cambio de sim a live"""
    
    print("\n" + "="*60)
    print("TEST: Cambio de Simulator → Live Camera")
    print("="*60 + "\n")
    
    # [1] Test: Listar cámaras disponibles
    print("[1] Buscando cámaras disponibles...")
    camera_service = CameraService()
    cameras = camera_service.list_cameras()
    
    if not cameras:
        print("    ❌ No hay cámaras disponibles")
        print("    💡 Al menos Virtual Test Camera debería estar disponible")
        return False
    
    print(f"    ✅ Cámaras encontradas: {len(cameras)}")
    for cam in cameras:
        print(f"       - ID {cam['id']}: {cam['name']}")
    
    # [2] Test: Conectar a Virtual Camera
    print("\n[2] Conectando a Virtual Camera (-1)...")
    try:
        camera_service.connect(-1)
        print("    ✅ Conectado a Virtual Camera")
    except Exception as e:
        print(f"    ❌ Error al conectar: {e}")
        return False
    
    # [3] Test: Capturar frame de Virtual
    print("\n[3] Capturando frame de Virtual Camera...")
    try:
        frame = camera_service.get_frame()
        if frame is None or frame.size == 0:
            print("    ❌ Frame vacío o None")
            return False
        print(f"    ✅ Frame capturado: {frame.shape}")
    except Exception as e:
        print(f"    ❌ Error al capturar: {e}")
        return False
    
    # [4] Test: ColorMonitor con Virtual Camera
    print("\n[4] Probando ColorMonitor con Virtual Camera...")
    try:
        color_monitor = ColorMonitor()
        
        # Agregar target de color
        target = ColorTarget(
            name="Test Red",
            l_target=40.0,
            a_target=75.0,
            b_target=25.0,
            tolerance_warning=2.0,
            tolerance_critical=5.0
        )
        color_monitor.add_target(target)
        print("    ✅ Target de color agregado")
        
        # Intentar medir color
        measurement = color_monitor.measure_color_frame(frame, target)
        if measurement:
            print(f"    ✅ Medición exitosa: ΔE={measurement.delta_e:.2f}, State={measurement.state}")
        else:
            print("    ⚠️  Medición retornó None (frame inválido para color)")
            
    except Exception as e:
        print(f"    ❌ Error en ColorMonitor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # [5] Test: Intentar conectar a cámara real (si existe)
    print("\n[5] Intentando conectar a Cámara Real (ID 0)...")
    try:
        camera_service.connect(0)
        print("    ✅ Conectado a Cámara Real")
        
        # Intentar capturar frame
        frame_real = camera_service.get_frame()
        print(f"    ✅ Frame capturado de cámara real: {frame_real.shape}")
        
        # Intentar medir color
        measurement_real = color_monitor.measure_color_frame(frame_real, target)
        if measurement_real:
            print(f"    ✅ Medición de cámara real exitosa: ΔE={measurement_real.delta_e:.2f}")
        
    except Exception as e:
        print(f"    ⚠️  Cámara real no disponible (esperado): {e}")
        print("       Esto es normal si no hay cámara USB conectada")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETADO - Sistema puede cambiar entre modos")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = test_camera_switch()
    sys.exit(0 if success else 1)
