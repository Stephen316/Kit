from dataclasses import asdict
from hashlib import sha256
from json import dumps
from math import hypot, pi, radians, tan
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


Root = Path(__file__).resolve().parent
Cases = (
    ("Expanding7deg", 10.0, 17.0, 7.0),
    ("Contracting5deg", 14.0, 23.0, -5.0),
    ("ZeroAngleLimit", 9.0, 11.0, 0.0),
)
Results = []
for Name, RadiusMm, HeightMm, Degrees in Cases:
    Spec = DocumentSpec(
        "Kit independent " + Name,
        "frustumHeight",
        HeightMm,
        ProfileKind="frustum",
        RadiusMm=RadiusMm,
        TaperDegrees=Degrees,
        ParamComment="Independent tapered extrusion driving height",
        SketchName="Independent base circle",
        ExtrusionName="Independent tapered extrusion",
        BodyName="Independent frustum",
        Material=MaterialSpec("Independent frustum material", 2870.0, ColorValue(0.2, 0.4, 0.6, 1.0)),
    )
    Payload = EmitDocument(Spec)
    Target = Root / (Name + ".f3d")
    Target.write_bytes(Payload)
    Lower, Height = RadiusMm / 10.0, HeightMm / 10.0
    Upper = Lower + Height * tan(radians(Degrees))
    Cross = Lower * Lower + Lower * Upper + Upper * Upper
    Volume = pi * Height * Cross / 3.0
    Delta = Upper - Lower
    Fourth = Height * sum(Lower ** (4 - Index) * Upper**Index for Index in range(5)) / 5.0
    Axial = Height**3 * (Lower**2 / 3.0 + Lower * Delta / 2.0 + Delta**2 / 5.0)
    Results.append({
        "name": Name,
        "path": str(Target),
        "sha256": sha256(Payload).hexdigest(),
        "bytes": len(Payload),
        "specification": asdict(Spec),
        "parameters": {"height": "frustumHeight", "alongDistance": "d2", "taperAngle": "d3"},
        "expected": {
            "bottomRadiusMm": RadiusMm,
            "topRadiusMm": Upper * 10.0,
            "heightMm": HeightMm,
            "taperRadians": radians(Degrees),
            "volumeCm3": Volume,
            "surfaceAreaCm2": pi * (Lower**2 + Upper**2 + (Lower + Upper) * hypot(Height, Delta)),
            "centerCm": [0.0, 0.0, Height * (Lower**2 + 2 * Lower * Upper + 3 * Upper**2) / (4 * Cross)],
            "originInertiaCm5": [pi * (Fourth / 4 + Axial)] * 2 + [pi * Fourth / 2],
            "massKg": Volume * 0.00287,
            "boundsCm": [[-max(Lower, Upper), -max(Lower, Upper), 0.0], [max(Lower, Upper), max(Lower, Upper), Height]],
            "topology": {"solids": 1, "faces": 3, "edges": 2, "vertices": 2},
            "timelineFeatures": 2,
            "sketchProfiles": 1,
        },
    })
Report = {
    "scope": "Complete independent F3D authoring from DocumentSpec dimensions and fresh material; no source archive, body, field snapshot or captured material payload is read",
    "cases": Results,
    "nativeAcceptance": "pending; artifacts generated only, no local tests or native calls",
}
(Root / "Preparation.json").write_text(dumps(Report, indent=2) + "\n")
print(dumps([{Key: Case[Key] for Key in ("name", "sha256", "bytes")} for Case in Results], indent=2))
