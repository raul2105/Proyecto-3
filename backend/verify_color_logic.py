from color_module import ColorMonitor, ColorTarget

def test_color_logic():
    monitor = ColorMonitor()
    
    # 1. Test Target Management
    target = ColorTarget(name="Test Red", l_target=50, a_target=80, b_target=60)
    monitor.add_target(target)
    assert monitor.get_active_target().name == "Test Red"
    print("Target Management: OK")
    
    # 2. Test DeltaE Calculation (Identity)
    de = monitor.calculate_delta_e((50, 80, 60), (50, 80, 60))
    # Floating point tolerance
    assert de < 0.001
    print(f"DeltaE Identity: {de:.4f} (OK)")
    
    # 3. Test DeltaE Calculation (Known Shift)
    # L shift
    de_l = monitor.calculate_delta_e((50, 80, 60), (55, 80, 60))
    print(f"DeltaE (L shift +5): {de_l:.4f}")
    
    # 4. Test Measurement Recording
    meas = monitor.record_measurement(55, 80, 60)
    assert meas.delta_e > 0
    assert meas.is_warning == (meas.delta_e > target.tolerance_warning)
    print("Measurement Recording: OK")
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_color_logic()
