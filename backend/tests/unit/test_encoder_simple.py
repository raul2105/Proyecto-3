"""
Simplified unit tests for encoder synchronization
"""
import pytest
from datetime import datetime, timedelta
from sync.encoder import EncoderSync, EncoderSimulator


@pytest.mark.unit
def test_encoder_basic_functionality():
    """Test basic encoder functionality"""
    sync = EncoderSync(mm_per_tick=0.1)
    
    # Process 100 pulses
    for _ in range(100):
        sync.process_pulse()
    
    # Should advance 10mm
    assert abs(sync.get_position_mm() - 10.0) < 0.01
    assert abs(sync.get_position_m() - 0.01) < 0.0001
    

@pytest.mark.unit  
def test_encoder_px_per_mm():
    """Test spatial resolution calculation"""
    sync = EncoderSync()
    
    # Common flexo setup: 1280px sensor, 330mm web width
    px_per_mm = sync.calculate_px_per_mm(1280, 330.0)
    
    # Should be approximately 3.88 px/mm
    assert 3.8 < px_per_mm < 3.9
