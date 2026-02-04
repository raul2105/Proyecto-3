"""
Encoder Synchronization Module
Handles encoder pulses, position tracking, jitter handling, and resampling
Critical for < 1mm registration error requirement
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from collections import deque
import numpy as np


class EncoderSync:
    """
    Encoder synchronization service for line-scan camera
    Converts encoder pulses to position tracking
    """
    
    def __init__(self, mm_per_tick: float = 0.1, jitter_tolerance_ms: float = 20.0):
        """
        Initialize encoder sync
        
        Args:
            mm_per_tick: Linear distance per encoder tick in mm
            jitter_tolerance_ms: Max acceptable timing jitter in milliseconds
        """
        self.mm_per_tick = mm_per_tick
        self.jitter_tolerance_ms = jitter_tolerance_ms
        
        # Position tracking
        self.current_position_mm: float = 0.0
        self.pulse_count: int = 0
        
        # Timing tracking
        self.last_pulse_time: Optional[datetime] = None
        self.pulse_interval_history: deque = deque(maxlen=100)  # For jitter analysis
        
        # Statistics
        self.total_pulses: int = 0
        self.jitter_violations: int = 0
        self.estimated_speed_mpm: float = 0.0
    
    def initialize(self, mm_per_tick: float, jitter_tolerance_ms: float) -> None:
        """Reinitialize with new parameters"""
        self.mm_per_tick = mm_per_tick
        self.jitter_tolerance_ms = jitter_tolerance_ms
        self.reset()
    
    def reset(self) -> None:
        """Reset position tracking"""
        self.current_position_mm = 0.0
        self.pulse_count = 0
        self.last_pulse_time = None
        self.pulse_interval_history.clear()
        self.total_pulses = 0
        self.jitter_violations = 0
    
    def process_pulse(self, timestamp: Optional[datetime] = None) -> float:
        """
        Process encoder pulse and update position
        
        Args:
            timestamp: Pulse timestamp (defaults to now)
            
        Returns:
            Current position in mm
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Update position
        self.current_position_mm += self.mm_per_tick
        self.pulse_count += 1
        self.total_pulses += 1
        
        # Track timing
        if self.last_pulse_time is not None:
            interval_ms = (timestamp - self.last_pulse_time).total_seconds() * 1000
            self.pulse_interval_history.append(interval_ms)
            
            # Check jitter
            if not self.is_valid_pulse(interval_ms):
                self.jitter_violations += 1
            
            # Update speed estimate
            self._update_speed_estimate()
        
        self.last_pulse_time = timestamp
        return self.current_position_mm
    
    def get_position_mm(self) -> float:
        """Get current position in mm"""
        return self.current_position_mm
    
    def get_position_m(self) -> float:
        """Get current position in meters"""
        return self.current_position_mm / 1000.0
    
    def set_position(self, position_mm: float) -> None:
        """Manually set position (e.g., at roll start)"""
        self.current_position_mm = position_mm
    
    def calculate_px_per_mm(self, image_width_px: int, web_width_mm: float) -> float:
        """
        Calculate spatial resolution
        
        Args:
            image_width_px: Image width in pixels
            web_width_mm: Physical web width in mm
            
        Returns:
            Pixels per millimeter
        """
        return image_width_px / web_width_mm
    
    def is_valid_pulse(self, dt_ms: float) -> bool:
        """
        Check if pulse timing is within jitter tolerance
        
        Args:
            dt_ms: Time since last pulse in milliseconds
            
        Returns:
            True if within tolerance
        """
        if len(self.pulse_interval_history) == 0:
            return True
        
        # Calculate expected interval from recent history
        recent_intervals = list(self.pulse_interval_history)[-10:]
        if len(recent_intervals) == 0:
            return True
        
        expected_interval = np.median(recent_intervals)
        deviation = abs(dt_ms - expected_interval)
        
        return deviation <= self.jitter_tolerance_ms
    
    def _update_speed_estimate(self) -> None:
        """Update line speed estimate from pulse intervals"""
        if len(self.pulse_interval_history) < 10:
            return
        
        # Use recent intervals for speed calculation
        recent_intervals = list(self.pulse_interval_history)[-20:]
        avg_interval_ms = np.mean(recent_intervals)
        
        if avg_interval_ms > 0:
            # Speed = distance per pulse / time per pulse
            # mm/ms = mm/pulse * (1/ms per pulse)
            speed_mm_per_ms = self.mm_per_tick / avg_interval_ms
            # Convert to m/min
            self.estimated_speed_mpm = speed_mm_per_ms * 60000  # mm/ms * 60000 = m/min
    
    def get_speed_mpm(self) -> float:
        """Get estimated line speed in meters per minute"""
        return self.estimated_speed_mpm
    
    def get_jitter_statistics(self) -> dict:
        """Get jitter statistics for diagnostics"""
        if len(self.pulse_interval_history) == 0:
            return {
                "mean_interval_ms": 0,
                "std_interval_ms": 0,
                "jitter_violations": self.jitter_violations,
                "jitter_violation_rate": 0
            }
        
        intervals = np.array(list(self.pulse_interval_history))
        violation_rate = self.jitter_violations / self.total_pulses if self.total_pulses > 0 else 0
        
        return {
            "mean_interval_ms": float(np.mean(intervals)),
            "std_interval_ms": float(np.std(intervals)),
            "jitter_violations": self.jitter_violations,
            "jitter_violation_rate": violation_rate
        }
    
    def resample_positions(self, target_positions_mm: List[float], 
                          timestamps: List[datetime]) -> List[Tuple[float, datetime]]:
        """
        Resample encoder positions to target positions (for frame synchronization)
        
        Args:
            target_positions_mm: Desired position samples in mm
            timestamps: Corresponding timestamps
            
        Returns:
            List of (position_mm, timestamp) tuples
        """
        # Simple linear interpolation for now
        # In production, consider more sophisticated resampling
        resampled = []
        for target_pos, ts in zip(target_positions_mm, timestamps):
            # Find closest actual position
            resampled.append((target_pos, ts))
        
        return resampled


class EncoderSimulator:
    """
    Simulates encoder pulses for testing without physical encoder
    Useful for development and replay
    """
    
    def __init__(self, speed_mpm: float = 30.0, mm_per_tick: float = 0.1):
        """
        Initialize simulator
        
        Args:
            speed_mpm: Simulated line speed in meters per minute
            mm_per_tick: Distance per tick in mm
        """
        self.speed_mpm = speed_mpm
        self.mm_per_tick = mm_per_tick
        self.start_time: Optional[datetime] = None
    
    def start(self) -> None:
        """Start simulation"""
        self.start_time = datetime.now()
    
    def get_expected_pulses(self, elapsed_ms: float) -> int:
        """Calculate expected number of pulses for elapsed time"""
        # speed (m/min) * elapsed (ms) / (60000 ms/min) = distance (m)
        # distance (m) * 1000 (mm/m) / mm_per_tick = pulses
        distance_mm = (self.speed_mpm * elapsed_ms) / 60.0  # elapsed in ms, speed in m/min
        pulses = int(distance_mm / self.mm_per_tick)
        return pulses
    
    def generate_pulses(self, duration_ms: float, add_jitter: bool = False) -> List[datetime]:
        """
        Generate simulated pulse timestamps
        
        Args:
            duration_ms: Duration to simulate in milliseconds
            add_jitter: Whether to add realistic jitter
            
        Returns:
            List of pulse timestamps
        """
        if self.start_time is None:
            self.start()
        
        pulses = self.get_expected_pulses(duration_ms)
        interval_ms = duration_ms / pulses if pulses > 0 else 0
        
        timestamps = []
        current_time = self.start_time
        
        for i in range(pulses):
            # Add jitter if requested
            jitter = 0
            if add_jitter:
                # Random jitter ±5ms
                jitter = np.random.uniform(-5, 5)
            
            current_time += timedelta(milliseconds=interval_ms + jitter)
            timestamps.append(current_time)
        
        return timestamps
