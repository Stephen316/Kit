from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

KDefaultCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(),
    ("StructuralBasicSchema", None, "PrismOpaqueSchema"),
)
KPlasticCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Plastic",
        1060.0,
        ColorValue(0.9, 0.9, 0.9, 1.0),
        "Plastic",
        MechanicSpec(2.24e9, 0.38, 8.0e8, 2.0e7, 2.9e7, 0.16, 1500.0, 8.57e-5),
        None,
        FinishSpec(Roughness=0.3, Reflectance=0.05, ColorSpace=1),
    ),
    ("StructuralPlasticSchema", None, "PrismOpaqueSchema"),
)
KGlassCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Glass",
        2500.0,
        ColorValue(0.9, 0.95, 0.9, 1.0),
        "Generic",
        MechanicSpec(7.0e10, 0.22),
        ThermalSpec(Emissivity=0.9, TransmitsLight=True),
        FinishSpec(Refraction=1.52, ColorDepth=50.0),
        "Glass",
    ),
    ("StructuralGenericSchema", "ThermalSolidSchema", "PrismTransparentSchema"),
)
KGasCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Gas",
        1.2,
        ColorValue(1.0, 1.0, 1.0, 1.0),
        "Gas",
        MechanicSpec(Conductivity=0.026, Expansion=0.0034),
        ThermalSpec(Viscosity=1.8e-5),
        FinishSpec(Refraction=1.0),
    ),
    ("StructuralGasSchema", "ThermalGasSchema", "PrismTransparentSchema"),
)
KLiquidCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Liquid",
        998.0,
        ColorValue(0.5, 0.6, 0.9, 1.0),
        "Liquid",
        MechanicSpec(),
        ThermalSpec(Viscosity=1.0e-3, VaporPressure=3000.0),
        FinishSpec(Refraction=1.33),
    ),
    ("StructuralLiquidSchema", "ThermalLiquidSchema", "PrismTransparentSchema"),
)
KWoodCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Wood",
        650.0,
        ColorValue(0.6, 0.4, 0.2, 1.0),
        "Wood",
        MechanicSpec(1.2e10, Conductivity=0.12, SpecificHeat=1700.0),
        ThermalSpec(),
        FinishSpec(Roughness=0.6),
    ),
    ("StructuralWoodSchema", "ThermalSolidSchema", "PrismOpaqueSchema"),
)
KMetalCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Metal",
        7850.0,
        ColorValue(0.6, 0.6, 0.6, 1.0),
        "Metal",
        MechanicSpec(2.0e11, 0.3, YieldStrength=2.5e8, TensileStrength=4.0e8),
        ThermalSpec(Resistivity=1.7e-7),
        FinishSpec(Metallic=True, Roughness=0.2, Anisotropy=0.1),
    ),
    ("StructuralMetalSchema", "ThermalSolidSchema", "PrismMetalSchema"),
)
KStoneCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Stone",
        2800.0,
        ColorValue(0.3, 0.3, 0.35, 1.0),
        "Basic",
        MechanicSpec(Conductivity=2.0, SpecificHeat=760.0, Damping=0.01),
        ThermalSpec(Emissivity=0.95),
        FinishSpec(Roughness=0.8, ColorSpace=2),
        "Stone",
    ),
    ("StructuralBasicSchema", "ThermalSolidSchema", "PrismOpaqueSchema"),
)
KLayeredCase: tuple[MaterialSpec, tuple[str, str | None, str]] = (
    MaterialSpec(
        "Kit Layered",
        1500.0,
        ColorValue(0.1, 0.1, 0.1, 1.0),
        "Plastic",
        MechanicSpec(7.0e9),
        None,
        FinishSpec(LayerFraction=0.3, LayerRoughness=0.1),
    ),
    ("StructuralPlasticSchema", None, "PrismLayeredSchema"),
)
KBaseCases = {
    "default": KDefaultCase,
    "plastic": KPlasticCase,
    "glass": KGlassCase,
    "gas": KGasCase,
    "liquid": KLiquidCase,
    "wood": KWoodCase,
    "metal": KMetalCase,
    "stone": KStoneCase,
    "layered": KLayeredCase,
}
KGrainCases: dict[str, tuple[MaterialSpec, tuple[str, str | None, str]]] = {
    "orthowood": (
        MaterialSpec(
            "Kit Orthotropic Wood",
            820.0,
            ColorValue(0.7, 0.5, 0.3, 1.0),
            "Wood",
            MechanicSpec(
                YoungModulus=1.2e10,
                Bending=1.0e8,
                CompressAlong=6.0e7,
                TensionAcross=4.6e6,
                Behavior="Orthotropic",
                Directional=(
                    DirectionValue("PoissonRatio", "X", 0.45),
                    DirectionValue("YoungModulus", "Y", 6.0e8),
                ),
            ),
            None,
            FinishSpec(Roughness=0.5),
        ),
        ("StructuralWoodSchema", None, "PrismOpaqueSchema"),
    ),
}
KFamilyCases = {**KBaseCases, **KGrainCases}
KClassTypes: dict[str, str] = {
    "orthowood": "Wood",
    "default": "Generic",
    "plastic": "Plastic",
    "gas": "Gas",
    "liquid": "Liquid",
    "wood": "Wood",
    "metal": "Metal",
    "layered": "Plastic",
}
