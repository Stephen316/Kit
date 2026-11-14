from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


@MakeDataClass(frozen=True, slots=True)
class FinishSpec:
    NameValue: str | None = None
    Metallic: bool = False
    ColorSpace: int | None = None
    Roughness: float | None = None
    Anisotropy: float | None = None
    Rotation: float | None = None
    Tint: ColorValue | None = None
    Reflectance: float | None = None
    Translucent: bool | None = None
    ScatterDistance: float | None = None
    ScatterColor: ColorValue | None = None
    Refraction: float | None = None
    ColorDepth: float | None = None
    LayerColor: ColorValue | None = None
    LayerFraction: float | None = None
    LayerRoughness: float | None = None
