"""
Replay Simulator Module
Loads and plays back recorded datasets for testing without live cameras
Supports encoder simulation and variable speeds
"""
import os
import json
import pickle
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import cv2
from pathlib import Path


class ReplayDataset:
    """
    Recorded dataset structure for replay
    Includes frames, encoder data, timestamps, and metadata
    """
    
    def __init__(self, name: str):
        self.name = name
        self.frames: List[np.ndarray] = []
        self.timestamps: List[datetime] = []
        self.encoder_positions: List[float] = []  # in mm
        self.metadata: Dict[str, Any] = {
            "recording_date": None,
            "web_width_mm": 330.0,
            "label_pitch_mm": 70.0,
            "speed_mpm": 30.0,
            "camera_resolution": (1280, 720),
            "defects_annotated": []
        }
    
    def add_frame(self, frame: np.ndarray, timestamp: datetime, position_mm: float):
        """Add a frame to the dataset"""
        self.frames.append(frame)
        self.timestamps.append(timestamp)
        self.encoder_positions.append(position_mm)
    
    def save(self, directory: str):
        """Save dataset to disk"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Save frames as compressed images
        frames_dir = os.path.join(directory, self.name, "frames")
        Path(frames_dir).mkdir(parents=True, exist_ok=True)
        
        for idx, frame in enumerate(self.frames):
            frame_path = os.path.join(frames_dir, f"frame_{idx:06d}.jpg")
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Save metadata and indices
        data_path = os.path.join(directory, self.name, "dataset.pkl")
        with open(data_path, 'wb') as f:
            pickle.dump({
                'name': self.name,
                'timestamps': self.timestamps,
                'encoder_positions': self.encoder_positions,
                'metadata': self.metadata,
                'frame_count': len(self.frames)
            }, f)
        
        print(f"Dataset saved: {len(self.frames)} frames to {directory}")
    
    @classmethod
    def load(cls, directory: str, name: str) -> 'ReplayDataset':
        """Load dataset from disk"""
        data_path = os.path.join(directory, name, "dataset.pkl")
        frames_dir = os.path.join(directory, name, "frames")
        
        # Load metadata
        with open(data_path, 'rb') as f:
            data = pickle.load(f)
        
        dataset = cls(name)
        dataset.timestamps = data['timestamps']
        dataset.encoder_positions = data['encoder_positions']
        dataset.metadata = data['metadata']
        
        # Load frames
        for idx in range(data['frame_count']):
            frame_path = os.path.join(frames_dir, f"frame_{idx:06d}.jpg")
            frame = cv2.imread(frame_path)
            dataset.frames.append(frame)
        
        print(f"Dataset loaded: {len(dataset.frames)} frames from {directory}")
        return dataset
