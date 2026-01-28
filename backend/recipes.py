import json
import os
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional

RECIPES_DIR = "recipes"

if not os.path.exists(RECIPES_DIR):
    os.makedirs(RECIPES_DIR)

from pydantic import BaseModel, Field
from color_module import ColorTarget


class ColorROI(BaseModel):
    """ROI de color - Point 5 integration"""
    roi_id: str
    name: str
    bounds: tuple  # (x1, y1, x2, y2)
    
    # Target
    lab_l: float
    lab_a: float
    lab_b: float
    
    # Tolerancias
    warn_deltae: float = 2.0
    oot_deltae: float = 5.0
    
    # Config
    deltae_formula: str = "94"  # "76" | "94" | "2000"


class AlarmRuleConfig(BaseModel):
    """Configuración de regla de alarma - Point 7 integration"""
    rule_id: str
    enabled: bool = True
    trigger_type: str  # "on_defect" | "on_rate" | "on_color_oot"
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    cooldown_ms: int = 2000
    description: str = ""


class Recipe(BaseModel):
    name: str
    client: str = ""
    job_number: str = ""
    camera_id: int = 0
    exposure: float = -5.0
    master_file: str = ""

    # JobRef
    master_pdf_uri: str = ""
    master_render_dpi: int = 150
    registration_mode: str = "TEMPLATE"  # FIDUCIALS, EDGE, TEMPLATE, HYBRID
    tolerances: Dict[str, float] = Field(default_factory=lambda: {"pos_px": 5.0, "scale_ppm": 500.0, "rotation_deg": 0.5, "diff_threshold": 30.0})
    
    # New Operational Parameters
    web_width_mm: float = 330.0
    lane_count: int = 1
    lanes: List[Dict[str, Any]] = Field(default_factory=list)
    repeat_mm: float = 0.0
    
    # Inspection Settings
    rois: List[Dict[str, Any]] = Field(default_factory=list)
    inspection_rois: List[Dict[str, Any]] = Field(default_factory=list)
    color_rois: List[ColorROI] = Field(default_factory=list)
    exclude_rois: List[Dict[str, Any]] = Field(default_factory=list)
    defect_thresholds: Dict[str, float] = Field(default_factory=lambda: {"min_area": 50.0, "sensitivity": 30.0, "critical_area": 500.0, "major_area": 150.0})
    defect_rules: Dict[str, Any] = Field(default_factory=dict)
    alarm_rules: List[AlarmRuleConfig] = Field(default_factory=list)
    
    # Color Settings - Point 5 integration
    color_targets: List[ColorTarget] = Field(default_factory=list)
    calibration_id: Optional[str] = None
    calibration_timestamp: Optional[datetime] = None
    
    # Color alarm config
    color_alarm_config: Dict[str, Any] = Field(default_factory=lambda: {
        "alert_on_oot": True,
        "alert_on_warn_duration_s": 10,
        "alert_on_oot_duration_s": 5
    })

    # Retention / Recording
    store_full_frame_on_defect: bool = False
    video_recording_mode: str = "OFF"  # OFF, ALWAYS, ON_DEFECT
    retention_days_images: int = 30
    retention_days_video: int = 14

class RecipeManager:
    def list_recipes(self):
        files = [f for f in os.listdir(RECIPES_DIR) if f.endswith(".json")]
        return [f.replace(".json", "") for f in files]

    def save_recipe(self, recipe: Recipe):
        filepath = os.path.join(RECIPES_DIR, f"{recipe.name}.json")
        with open(filepath, "w") as f:
            json.dump(recipe.dict(), f, default=str, indent=4) # default=str for datetime if needed
        return {"status": "saved", "name": recipe.name}

    def load_recipe(self, name: str):
        filepath = os.path.join(RECIPES_DIR, f"{name}.json")
        if not os.path.exists(filepath):
            raise Exception("Recipe not found")
        
        with open(filepath, "r") as f:
            data = json.load(f)
        return data

    def clone_recipe(self, original_name: str, new_name: str):
        data = self.load_recipe(original_name)
        data["name"] = new_name
        
        new_recipe = Recipe(**data)
        return self.save_recipe(new_recipe)
