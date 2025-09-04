from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DesignCode(str, Enum):
    AISC = "AISC"
    IS800 = "IS800"


class FrameType(str, Enum):
    ClearSpan = "ClearSpan"
    MultiSpan = "MultiSpan"
    MultiGable = "MultiGable"
    MonoSlope = "MonoSlope"


class InputModel(BaseModel):
    # Core fields used by the generator
    design_code: DesignCode | str = Field(alias="design_code")
    frame_type: FrameType | str = Field(alias="frame_type")
    span_m: float
    eave_height_m: float | None = None
    bay_spacing_m: float | None = None
    dead_load_kPa: float | None = None
    live_load_kPa: float | None = None
    collateral_kPa: float | None = None
    wind_speed_mps: float | None = None
    seismic_zone: str | None = None
    steel_grade: str | None = None
    members_count: int = Field(alias="Members_count")

    # Additional, user-specific columns (optional; pass-through)
    building_type: Optional[str] = Field(default=None, alias="Building type")
    width_o_o_of_steel_m: Optional[float] = Field(default=None, alias="Width in m (o/o of steel)")
    right_eave_height_m: Optional[float] = Field(default=None, alias="Right eave height in m")
    right_end_wall_bay_spacing_m: Optional[float] = Field(
        default=None, alias="Right end wall bay spacing in m"
    )
    side_wall_bay_spacing_expr: Optional[str] = Field(
        default=None, alias="Side wall bay spacing"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }

    @field_validator("span_m")
    @classmethod
    def _positive_span(cls, v: float) -> float:
        if v is None or v <= 0:
            raise ValueError("span_m must be positive")
        return v

    @field_validator("seismic_zone", mode="before")
    @classmethod
    def _seismic_to_str(cls, v: Optional[str | float]) -> Optional[str]:
        if v is None:
            return v
        return str(v)

    @field_validator("steel_grade", mode="before")
    @classmethod
    def _steel_to_str(cls, v: Optional[str | float | int]) -> Optional[str]:
        if v is None:
            return v
        return str(v)

    @field_validator("members_count")
    @classmethod
    def _members_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Members_count must be positive")
        return v


class PlateWeb(BaseModel):
    thickness_mm: float
    depth_step_mm: int


class PlateFlange(BaseModel):
    width_mm: float
    thickness_mm: float


class ConfigModel(BaseModel):
    density_kg_per_m3: float = 7850.0

    # Feature flags
    features: dict = Field(default_factory=lambda: {
        "R1_min_thickness": True,
        "R2_max_bt": True,
        "R3_depth_range": True,
    })

    # Min thickness by component
    min_thickness_mm: dict = Field(default_factory=lambda: {
        "web": 4.0,
        "flange": 6.0,
    })

    # Max b/t by code for flanges
    max_bt: dict = Field(default_factory=lambda: {
        "AISC": 12.0,
        "IS800": 10.0,
    })

    # Mapping heuristics for depth ranges
    depth_mapping: dict = Field(default_factory=dict)


class MemberCandidate(BaseModel):
    member_id: str
    web_start_depth_mm: int
    web_end_depth_mm: int
    web_thickness_mm: float
    if_width_mm: float
    if_thickness_mm: float
    of_width_mm: float
    of_thickness_mm: float
    weight_kg_per_m: float
    status: str = "Not evaluated"


class LibraryModel(BaseModel):
    webs: List[PlateWeb]
    flanges: List[PlateFlange]


