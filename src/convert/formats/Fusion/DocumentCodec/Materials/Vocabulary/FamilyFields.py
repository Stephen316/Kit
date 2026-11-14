KMechanicFields: dict[str, tuple[str, ...]] = {
    "YoungModulus": ("structural_Young_modulus",),
    "PoissonRatio": ("structural_Poisson_ratio",),
    "ShearModulus": ("structural_Shear_modulus",),
    "YieldStrength": ("structural_Minimum_yield_stress",),
    "TensileStrength": ("structural_Minimum_tensile_strength",),
    "Conductivity": ("structural_Thermal_conductivity",),
    "SpecificHeat": ("structural_Specific_heat",),
    "Expansion": ("structural_Thermal_expansion_coefficient",),
    "Damping": ("structural_Damping_coefficient",),
    "AverageModulus": ("structural_wood_Average_modulus",),
    "Bending": ("structural_wood_Bending",),
    "CompressAlong": ("structural_wood_compression_parallel",),
    "CompressAcross": ("structural_wood_compression_perpendicular",),
    "ShearAlong": ("structural_wood_shear_parallel",),
    "TensionAlong": ("structural_wood_tension_parallel",),
    "TensionAcross": ("structural_wood_tension_perpendicular",),
}
KThermalFields: dict[str, tuple[str, ...]] = {
    "Density": ("thermal_Density",),
    "Conductivity": ("thermal_Thermal_conductivity",),
    "SpecificHeat": ("thermal_Specific_heat",),
    "Emissivity": ("thermal_Emissivity",),
    "Resistivity": ("thermal_Electrical_resistivity",),
    "Permeability": ("thermal_Permeability",),
    "Porosity": ("thermal_Porosity",),
    "Reflectivity": ("thermal_Reflectivity",),
    "TransmitsLight": ("thermal_Transmits_light",),
    "Compressibility": ("thermal_Compressibility",),
    "Viscosity": ("thermal_Gas_viscosity", "thermal_Liquid_viscosity"),
    "VaporPressure": ("thermal_Vapor_pressure",),
    "Vaporization": ("thermal_Specific_heat_of_vaporization",),
}
KFinishFields: dict[str, tuple[str, ...]] = {
    "Roughness": ("surface_roughness",),
    "Anisotropy": ("surface_anisotropy",),
    "Rotation": ("surface_rotation",),
    "Tint": ("surface_albedo",),
    "Reflectance": ("opaque_f0", "layered_f0"),
    "Translucent": ("opaque_translucency",),
    "ScatterDistance": ("opaque_mfp",),
    "ScatterColor": ("opaque_mfp_modifier",),
    "Refraction": ("transparent_ior",),
    "ColorDepth": ("transparent_distance",),
    "LayerColor": ("layered_bottom_f0",),
    "LayerFraction": ("layered_fraction",),
    "LayerRoughness": ("layered_roughness",),
}
KColorFields: tuple[str, ...] = (
    "metal_f0",
    "opaque_albedo",
    "transparent_color",
    "layered_diffuse",
)
KInteriorModels = {"Opaque": 0, "Metal": 1, "Layered": 2, "Transparent": 3}
KFinishOrder = ("Opaque", "Layered", "Transparent")
KDirections = ("1", "2", "12", "23", "X", "Y", "Z")
