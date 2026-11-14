from dataclasses import asdict
from hashlib import sha256
from json import dumps
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec


Root = Path(__file__).resolve().parents[4]
Output = Root / "re/Fusion/LocalOracle/DimensionAuthoring"
Output.mkdir(parents=True, exist_ok=True)
Reports = []
for Profile in ("rectangle", "cuboid"):
    Specification = DocumentSpec(
        "Independent constrained " + Profile,
        "boxHeight", 31.0, ProfileKind=Profile,
        WidthMm=17.0, DepthMm=23.0,
        ConstrainRectangle=True,
        WidthParamName="boxWidth", DepthParamName="boxDepth",
        SketchName="Constrained rectangle",
        ExtrusionName="Dimension driven cuboid",
        BodyName="Dimension driven body",
        Material=MaterialSpec("Dimension driven material", 2870.0),
    )
    Payload = EmitDocument(Specification)
    Target = Output / ("Dimensioned" + Profile.title() + ".f3d")
    Target.write_bytes(Payload)
    Reports.append({
        "profile": Profile,
        "path": str(Target),
        "sha256": sha256(Payload).hexdigest(),
        "bytes": len(Payload),
        "specification": asdict(Specification),
        "expected": {
            "cornerCoordinatesCm": [[0, 0, 0], [1.7, 0, 0], [1.7, 2.3, 0], [0, 2.3, 0]],
            "sketchProfiles": 1,
            "geometricConstraints": 4,
            "dimensions": 2,
            "fullyConstrained": True,
            "volumeCm3": 12.121 if Profile == "cuboid" else None,
            "massKg": 12.121 * 0.00287 if Profile == "cuboid" else None,
            "centerCm": [0.85, 1.15, 1.55] if Profile == "cuboid" else None,
        },
        "suggestedNativeEdits": {"boxWidth": "19 mm", "boxDepth": "29 mm", "boxHeight": "37 mm"},
        "editedExpected": {
            "cornerCoordinatesCm": [[0, 0, 0], [1.9, 0, 0], [1.9, 2.9, 0], [0, 2.9, 0]],
            "volumeCm3": 1.9 * 2.9 * 3.7 if Profile == "cuboid" else None,
            "centerCm": [0.95, 1.45, 1.85] if Profile == "cuboid" else None,
        },
    })
Report = {
    "scope": "Complete F3D authoring from dimensions and fresh semantic identities; production API has no native runtime, source archive, captured entity record, or payload/template input",
    "cases": Reports,
    "verification": "Artifact generation only; native acceptance pending; no local tests",
}
(Output / "Preparation.json").write_text(dumps(Report, indent=2) + "\n")
print(dumps([{Key: Value[Key] for Key in ("profile", "sha256", "bytes")} for Value in Reports], indent=2))
