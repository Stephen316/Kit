from pathlib import Path as FilePath

# repo root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRepoRoot = FilePath(__file__).resolve().parents[6]

# the graphic sources cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KGraphicSources = (
    KRepoRoot
    / "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    KRepoRoot
    / "re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d",
)
