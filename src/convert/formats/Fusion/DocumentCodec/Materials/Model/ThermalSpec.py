from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ThermalSpec:
    Density: float | None = None
    Conductivity: float | None = None
    SpecificHeat: float | None = None
    Emissivity: float | None = None
    Resistivity: float | None = None
    Permeability: float | None = None
    Porosity: float | None = None
    Reflectivity: float | None = None
    TransmitsLight: bool | None = None
    Compressibility: float | None = None
    Viscosity: float | None = None
    VaporPressure: float | None = None
    Vaporization: float | None = None
